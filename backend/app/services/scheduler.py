"""
Automated daily refresh: pulls fresh postings, re-embeds/re-indexes them,
then backs the index and DB up to GCS.

Runs inside the same FastAPI process/VM rather than as a standalone
function, since the existing deploy target is a single GCP VM 
"""
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from ..models.base import SessionLocal, DATABASE_URL
from .ingest import run_ingest
from .gcs_sync import backup_index_to_gcs, backup_postgres_to_gcs

logger = logging.getLogger("jxbs.scheduler")

DEFAULT_QUERIES = ["software engineer", "machine learning engineer", "data scientist"]
DEFAULT_LOCATIONS = ["San Francisco, CA", "Seattle, WA", "New York, NY", "Remote"]

_scheduler: BackgroundScheduler | None = None


def _run_daily_refresh():
    db = SessionLocal()
    try:
        result = run_ingest(db, DEFAULT_QUERIES, DEFAULT_LOCATIONS)
        logger.info(f"[scheduler] daily ingest: {result}")
    except Exception:
        logger.exception("[scheduler] daily ingest failed")
    finally:
        db.close()

    try:
        index_result = backup_index_to_gcs()
        logger.info(f"[scheduler] index backup: {index_result}")
        db_result = backup_postgres_to_gcs(DATABASE_URL)
        logger.info(f"[scheduler] postgres backup: {db_result}")
    except Exception:
        logger.exception("[scheduler] backup failed")


def start_scheduler(hour: int = 6, minute: int = 0) -> BackgroundScheduler:
    """Idempotent: calling this more than once (e.g. under a dev reloader) reuses the existing scheduler."""
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    _scheduler = BackgroundScheduler()
    _scheduler.add_job(
        _run_daily_refresh,
        trigger=CronTrigger(hour=hour, minute=minute),
        id="daily_refresh",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info(f"[scheduler] started — daily refresh scheduled for {hour:02d}:{minute:02d} UTC")
    return _scheduler
