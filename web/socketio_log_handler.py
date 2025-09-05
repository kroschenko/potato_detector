import os
import sys
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Deque

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

class SocketIOLogHandler(logging.Handler):
    def __init__(self, socketio, recent_log_entries: Deque[dict]):
        super().__init__()
        self.socketio = socketio
        self.recent_log_entries = recent_log_entries

    def emit(self, record: logging.LogRecord) -> None:
        try:
            log_entry = self._serialize_record(record)
            self.recent_log_entries.append(log_entry)
            self.socketio.emit('log_entry', log_entry)
        except Exception:
            pass

    def _serialize_record(self, record: logging.LogRecord) -> Dict[str, Any]:
        level = record.levelname.lower()
        message = record.getMessage()
        timestamp = datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat()
        return {
            'level': level,
            'message': message,
            'timestamp': timestamp,
        }


