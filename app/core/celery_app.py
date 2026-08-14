"""
Celery application instance.

Configured to use Redis as both broker and result backend.
Auto-discovers task modules under ``app.tasks``.
Includes a Celery Beat schedule for periodic analysis.
"""

from celery import Celery
from celery.schedules import crontab
from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "finops",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    # Serialization
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    # Timezone
    timezone="UTC",
    enable_utc=True,

    # Reliability
    task_acks_late=True,                 # ack after execution, not before
    worker_prefetch_multiplier=1,        # one task at a time per worker
    task_reject_on_worker_lost=True,     # re-queue if worker dies

    # Result expiry
    result_expires=3600,                 # 1 hour

    # ── Celery Beat periodic schedule ────────────────────────────
    beat_schedule={
        "run-analysis-every-6-hours": {
            "task": "tasks.run_analysis_all",
            "schedule": crontab(minute=0, hour="*/6"),  # 00:00, 06:00, 12:00, 18:00 UTC
            "options": {"queue": "analysis"},
        },
    },
)

# Auto-discover tasks in app/tasks/*.py
celery_app.autodiscover_tasks(["app.tasks"])

