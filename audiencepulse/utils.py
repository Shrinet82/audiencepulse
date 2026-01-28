# Utility functions for AudiencePulse
import time
import logging
from functools import wraps

logger = logging.getLogger("audiencepulse")

def backoff_retry(max_tries: int = 5, base_delay: float = 1.0):
    """Decorator that retries a function with exponential back-off."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            delay = base_delay
            last_exception = None
            for attempt in range(1, max_tries + 1):
                try:
                    return fn(*args, **kwargs)
                except Exception as exc:
                    last_exception = exc
                    logger.warning(
                        f"Attempt {attempt}/{max_tries} failed: {exc}"
                    )
                    if attempt == max_tries:
                        raise
                    logger.info(f"Retrying in {delay:.1f}s...")
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff
            raise last_exception
        return wrapper
    return decorator

def parse_vote_count(vote_str: str) -> int:
    """Parse vote strings like '1.2K' or '5M' into integers."""
    if not vote_str:
        return 0
    vote_str = str(vote_str).strip().lower()
    try:
        if 'k' in vote_str:
            return int(float(vote_str.replace('k', '')) * 1000)
        elif 'm' in vote_str:
            return int(float(vote_str.replace('m', '')) * 1000000)
        else:
            return int(vote_str)
    except (ValueError, TypeError):
        return 0
