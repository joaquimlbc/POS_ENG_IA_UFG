"""Tests for the daily sync scheduler (US-012).

Priority: ALTO
Covers: scheduler construction/configuration, the job's success/error
logging, and that a failed run never lets an exception escape (the
"fallback" the backlog asks for).
"""

from unittest.mock import MagicMock, patch

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.scheduler import JOB_ID, create_scheduler, run_scheduled_ingest
from app.scripts.ingest import IngestReport


def _fake_report(**overrides: object) -> IngestReport:
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    defaults: dict = dict(
        started_at=now,
        completed_at=now,
        fetched=10,
        normalized=10,
        transformed=10,
        inserted=8,
        updated=2,
        failed=0,
        status="success",
        message="Ingested 10/10 countries",
    )
    defaults.update(overrides)
    return IngestReport(**defaults)


class TestCreateScheduler:
    """Tests for the scheduler factory."""

    def test_returns_background_scheduler(self) -> None:
        """Verify create_scheduler() builds a BackgroundScheduler instance."""
        scheduler = create_scheduler()

        assert isinstance(scheduler, BackgroundScheduler)

    def test_registers_daily_job_at_midnight_utc(self) -> None:
        """Verify the job is scheduled for 00:00 UTC daily via a cron trigger.

        Why: US-012 explicitly requires a 00:00 UTC daily run, not "roughly
        once a day" - this pins the exact trigger configuration.
        """
        scheduler = create_scheduler()

        job = scheduler.get_job(JOB_ID)

        assert job is not None
        assert isinstance(job.trigger, CronTrigger)
        fields = {f.name: str(f) for f in job.trigger.fields}
        assert fields["hour"] == "0"
        assert fields["minute"] == "0"

    def test_job_target_is_run_scheduled_ingest(self) -> None:
        """Verify the registered job actually calls run_scheduled_ingest."""
        scheduler = create_scheduler()

        job = scheduler.get_job(JOB_ID)

        assert job is not None
        assert job.func is run_scheduled_ingest

    def test_scheduler_starts_and_stops_cleanly(self) -> None:
        """Verify the scheduler can be started and shut down without error.

        Why: This is the exact lifecycle app.main's lifespan hook drives;
        a scheduler that can't stop cleanly would hang app shutdown/tests.
        """
        scheduler = create_scheduler()

        scheduler.start()
        try:
            assert scheduler.running is True
        finally:
            scheduler.shutdown(wait=False)

        assert scheduler.running is False


class TestRunScheduledIngest:
    """Tests for the job target function itself."""

    def test_successful_run_calls_ingest_countries_and_logs(self) -> None:
        """Verify a successful run invokes the pipeline and logs the outcome."""
        with patch(
            "app.scheduler.ingest_countries", return_value=_fake_report()
        ) as mock_ingest, patch("app.scheduler.logger") as mock_logger:
            run_scheduled_ingest()

        mock_ingest.assert_called_once_with()
        assert mock_logger.info.call_count == 2  # "started" + "completed"
        completed_message = mock_logger.info.call_args_list[-1].args[0]
        assert "inserted=8" in completed_message
        assert "updated=2" in completed_message

    def test_failed_run_is_logged_not_raised(self) -> None:
        """Verify an exception from ingest_countries is caught and logged.

        Why: This is the "fallback em caso de indisponibilidade da API"
        criterion - APScheduler would otherwise mark the job as errored
        and, depending on configuration, could drop future runs. The job
        target must swallow the failure itself.
        """
        with patch(
            "app.scheduler.ingest_countries",
            side_effect=ConnectionError("REST Countries API unreachable"),
        ), patch("app.scheduler.logger") as mock_logger:
            run_scheduled_ingest()  # must not raise

        mock_logger.error.assert_called_once()
        error_message = mock_logger.error.call_args.args[0]
        assert "ConnectionError" in error_message
        assert "REST Countries API unreachable" in error_message

    def test_partial_failure_report_is_logged_as_info(self) -> None:
        """Verify a partial_failure report (no exception) still logs cleanly."""
        report = _fake_report(status="partial_failure", failed=1, inserted=9)

        with patch("app.scheduler.ingest_countries", return_value=report), patch(
            "app.scheduler.logger"
        ) as mock_logger:
            run_scheduled_ingest()

        mock_logger.error.assert_not_called()
        completed_message = mock_logger.info.call_args_list[-1].args[0]
        assert "status=partial_failure" in completed_message


class TestSchedulerIntegrationWithApp:
    """Tests for the scheduler's lifecycle hook in app.main."""

    def test_lifespan_starts_and_stops_scheduler_when_enabled(self) -> None:
        """Verify the app's lifespan starts the scheduler on startup.

        Why: A scheduler created but never started would silently never
        run the daily sync - this proves the wiring in app.main actually
        starts it, not just that create_scheduler() works in isolation.
        """
        from fastapi.testclient import TestClient

        fake_scheduler = MagicMock()

        with patch("app.main.ENABLE_SCHEDULER", True), patch(
            "app.main.create_scheduler", return_value=fake_scheduler
        ):
            from app.main import app

            with TestClient(app):
                fake_scheduler.start.assert_called_once()
                fake_scheduler.shutdown.assert_not_called()

            fake_scheduler.shutdown.assert_called_once()

    def test_lifespan_skips_scheduler_when_disabled(self) -> None:
        """Verify ENABLE_SCHEDULER=false prevents the scheduler from starting.

        Why: Lets the API run standalone (e.g. one-off scripts, certain
        test setups) without a background job silently running.
        """
        from fastapi.testclient import TestClient

        with patch("app.main.ENABLE_SCHEDULER", False), patch(
            "app.main.create_scheduler"
        ) as mock_create:
            from app.main import app

            with TestClient(app):
                pass

            mock_create.assert_not_called()
