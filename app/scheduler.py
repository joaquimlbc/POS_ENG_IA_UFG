"""Automatic daily synchronization scheduler (US-012).

Wraps app.scripts.ingest.ingest_countries() in an APScheduler background
job that runs once a day at 00:00 UTC, with structured logging and a
fallback that keeps the scheduler alive if a run fails (e.g. the REST
Countries API is temporarily unavailable) rather than letting the
exception kill the job or the app.
"""

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.scripts.ingest import ingest_countries
from app.utils.logger import get_logger

logger = get_logger(__name__)

JOB_ID = "daily_country_sync"


def run_scheduled_ingest() -> None:
    """Job target: run the ingestion pipeline once and log the outcome.

    Never lets an exception escape to APScheduler. A failed run (e.g. the
    REST Countries API is down, or the database is briefly unreachable)
    is logged as an error and the job's next scheduled run is unaffected -
    this is the "fallback" the backlog asks for: one bad night doesn't
    silently kill the whole daily sync.
    """
    logger.info("Scheduled sync started")
    try:
        report = ingest_countries()
        logger.info(
            f"Scheduled sync completed: status={report.status}, "
            f"fetched={report.fetched}, inserted={report.inserted}, "
            f"updated={report.updated}, failed={report.failed}, "
            f"duration={report.duration_seconds:.2f}s"
        )
    except Exception as e:
        logger.error(f"Scheduled sync failed: {type(e).__name__}: {e}")


def create_scheduler() -> BackgroundScheduler:
    """Build (but do not start) the daily sync scheduler.

    Uses a thread-pool executor since ingest_countries() does blocking
    I/O (HTTP requests, DB writes); running it on APScheduler's default
    executor would otherwise share a single worker thread with any other
    scheduled job.

    Returns:
        A configured BackgroundScheduler with the daily job registered.
    """
    scheduler = BackgroundScheduler(
        timezone="UTC", executors={"default": ThreadPoolExecutor(1)}
    )
    scheduler.add_job(
        run_scheduled_ingest,
        trigger=CronTrigger(hour=0, minute=0, timezone="UTC"),
        id=JOB_ID,
        name="Daily REST Countries sync",
        replace_existing=True,
        misfire_grace_time=3600,  # tolerate up to 1h delay (app downtime at midnight)
    )
    return scheduler
