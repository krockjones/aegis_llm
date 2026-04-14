from __future__ import annotations

import logging
import sys


def setup_logging(level: str) -> None:
    """Structured key=value logs on stderr for grep-friendly ops."""
    numeric = getattr(logging, level.upper(), logging.INFO)
    root = logging.getLogger("aegis_llm")
    root.setLevel(numeric)
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(numeric)
    handler.setFormatter(_KeyValueFormatter())
    root.handlers.clear()
    root.addHandler(handler)
    root.propagate = False


class _KeyValueFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        parts = [
            f"level={record.levelname}",
            f"logger={record.name}",
            f"msg={record.getMessage()}",
        ]
        if hasattr(record, "request_id"):
            parts.append(f"request_id={getattr(record, 'request_id')}")
        if hasattr(record, "path"):
            parts.append(f"path={getattr(record, 'path')}")
        if hasattr(record, "method"):
            parts.append(f"method={getattr(record, 'method')}")
        if hasattr(record, "request_duration_ms"):
            parts.append(f"request_duration_ms={getattr(record, 'request_duration_ms')}")
        if hasattr(record, "status_code"):
            parts.append(f"status_code={getattr(record, 'status_code')}")
        if record.exc_info:
            parts.append(f"exc_info={self.formatException(record.exc_info)}")
        return " ".join(parts)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"aegis_llm.{name}")
