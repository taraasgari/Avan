import json
import logging
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    """Small dependency-free JSON formatter for container logs."""

    def format(self, record):
        payload = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in (
            "request_id",
            "method",
            "path",
            "status_code",
            "duration_ms",
            "user_id",
            "remote_hash",
        ):
            value = getattr(record, key, None)
            if value not in (None, ""):
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)
