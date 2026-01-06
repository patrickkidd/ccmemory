import logging
import os
import time
from functools import wraps

logger = logging.getLogger("ccmemory")


def logTool(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        project = kwargs.get("project") or os.path.basename(os.getcwd())
        try:
            result = await func(*args, **kwargs)
            logger.info(
                "",
                extra={
                    "cat": "tool",
                    "event": func.__name__,
                    "project": project,
                    "duration_ms": int((time.time() - start) * 1000),
                },
            )
            return result
        except Exception:
            logger.exception(
                "",
                extra={
                    "cat": "tool",
                    "event": func.__name__,
                    "project": project,
                },
            )
            raise

    return wrapper
