"""
Migration script — create all database tables.

Run:
    python -m migrations.create_tables

This imports every model so that ``Base.metadata`` is aware of all
tables, then issues ``CREATE TABLE IF NOT EXISTS`` statements against
the configured ``DATABASE_URL``.
"""

import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
)
logger = logging.getLogger(__name__)


def run_migration() -> None:
    """Create all tables defined in the ORM models."""

    # Import Base and engine
    from app.db.base import Base
    from app.db.session import engine

    # Import all models so they register with Base.metadata
    from app.models.tenant import Tenant           # noqa: F401
    from app.models.cost_daily import CostDaily     # noqa: F401
    from app.models.resource import Resource        # noqa: F401
    from app.models.recommendation import Recommendation  # noqa: F401

    logger.info("Creating tables in: %s", engine.url)

    Base.metadata.create_all(bind=engine)

    # List what was created
    table_names = sorted(Base.metadata.tables.keys())
    logger.info("Tables ensured: %s", ", ".join(table_names))
    logger.info("✅  Migration complete.")


if __name__ == "__main__":
    try:
        run_migration()
    except Exception as exc:
        logger.error("Migration failed: %s", exc)
        sys.exit(1)
