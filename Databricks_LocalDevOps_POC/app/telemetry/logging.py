"""Minimal JSON logging configuration without request content."""

import json
import logging
from datetime import UTC, datetime


class JsonFormatter(logging.Formatter):
    """Format standard log records as compact JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        return json.dumps(
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "level": record.levelname.lower(),
                "logger": record.name,
                "message": record.getMessage(),
            },
            ensure_ascii=True,
        )


def configure_logging() -> None:
    """Install a JSON formatter once for application-owned logs."""
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
