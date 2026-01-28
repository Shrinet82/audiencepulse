# AudiencePulse Core Library
"""
audiencepulse - YouTube Comment Intelligence Platform
"""
import logging
import json
import sys

__version__ = "1.0.0"

# Centralised JSON Logging
class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "msg": record.getMessage(),
            "module": record.module,
        })

# Setup logger
logger = logging.getLogger("audiencepulse")
logger.setLevel(logging.INFO)

# Avoid duplicate handlers
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
