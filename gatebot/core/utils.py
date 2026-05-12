import logging
from datetime import datetime, timezone


def utcnow() -> datetime:
    """Naive UTC timestamp. SQLAlchemy columns are TIMESTAMP WITHOUT TZ; we treat them as UTC."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def setup_logging_settings():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

