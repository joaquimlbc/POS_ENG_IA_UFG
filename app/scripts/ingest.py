"""End-to-end country ingestion pipeline (US-009).

Orchestrates: REST Countries API fetch -> normalization -> transformation ->
persistence, producing a summary report. Executable as:

    python -m app.scripts.ingest
"""

import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.api.rest_countries import (
    fetch_countries,
    normalize_countries,
    transform_normalized_countries,
)
from app.database.connection import SessionLocal, init_db
from app.database.repository import CountryRepository
from app.utils.errors import BatchProcessError
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class IngestReport:
    """Summary of a single ingestion run."""

    started_at: datetime
    completed_at: datetime
    fetched: int = 0
    normalized: int = 0
    transformed: int = 0
    inserted: int = 0
    updated: int = 0
    failed: int = 0
    normalization_errors: List[str] = field(default_factory=list)
    transformation_errors: List[str] = field(default_factory=list)
    status: str = "success"  # "success", "partial_failure", "failure"
    message: str = ""

    @property
    def duration_seconds(self) -> float:
        """Total wall-clock time of the run, in seconds."""
        return (self.completed_at - self.started_at).total_seconds()


def ingest_countries(session: Optional[Session] = None) -> IngestReport:
    """Run the full ingestion pipeline: fetch, normalize, transform, persist.

    Args:
        session: Optional SQLAlchemy session. When omitted, a new session
            is created from the application's session factory and closed
            automatically at the end of the run.

    Returns:
        IngestReport summarizing counts, errors and outcome of the run.
    """
    started_at = datetime.now(timezone.utc)
    owns_session = session is None
    session = session or SessionLocal()

    report = IngestReport(started_at=started_at, completed_at=started_at)

    try:
        logger.info("Starting country ingestion")

        raw_data = fetch_countries()
        report.fetched = len(raw_data)
        logger.info(f"Fetched {report.fetched} raw country records")

        normalized, normalization_errors = normalize_countries(raw_data)
        report.normalized = len(normalized)
        report.normalization_errors = normalization_errors

        transformed, transformation_errors = transform_normalized_countries(normalized)
        report.transformed = len(transformed)
        report.transformation_errors = transformation_errors

        repo = CountryRepository(session)
        try:
            _, inserted, updated = repo.upsert_with_relations(transformed)
            report.inserted = inserted
            report.updated = updated
        except BatchProcessError as e:
            report.inserted = e.successful
            report.failed = e.failed

        has_errors = bool(
            report.normalization_errors or report.transformation_errors or report.failed
        )
        report.status = "partial_failure" if has_errors else "success"
        report.message = (
            f"Ingested {report.inserted + report.updated}/{report.fetched} countries "
            f"({report.inserted} inserted, {report.updated} updated, "
            f"{report.failed} persistence failures, "
            f"{len(report.normalization_errors)} normalization errors, "
            f"{len(report.transformation_errors)} transformation errors)"
        )

    except Exception as e:
        report.status = "failure"
        report.message = f"Ingestion failed: {e}"
        logger.error(report.message)
        raise
    finally:
        report.completed_at = datetime.now(timezone.utc)
        if owns_session:
            session.close()

    logger.info(
        f"Ingestion completed in {report.duration_seconds:.2f}s: {report.message}"
    )
    return report


def main() -> int:
    """CLI entry point. Returns process exit code (0 success, 1 failure)."""
    init_db()
    try:
        report = ingest_countries()
    except Exception:
        return 1

    print(f"Status: {report.status}")
    print(f"Duration: {report.duration_seconds:.2f}s")
    print(f"Fetched: {report.fetched}")
    print(f"Inserted: {report.inserted}")
    print(f"Updated: {report.updated}")
    print(f"Failed: {report.failed}")
    print(f"Message: {report.message}")

    return 0 if report.status != "failure" else 1


if __name__ == "__main__":
    sys.exit(main())
