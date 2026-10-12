import app.services.scheduler as sched_module
from app.services.scheduler import start_scheduler


def test_start_scheduler_is_idempotent():
    sched_module._scheduler = None  # reset module-level state for a clean test
    try:
        first = start_scheduler(hour=3, minute=0)
        second = start_scheduler(hour=9, minute=0)  # different args, should be ignored
        assert first is second
    finally:
        if sched_module._scheduler is not None:
            sched_module._scheduler.shutdown(wait=False)
            sched_module._scheduler = None
