"""Activity logging for ccmemory - adds file handler for host-mounted log."""

import logging
import os

ACTIVITY_LOG_PATH = os.environ.get("CCMEMORY_ACTIVITY_LOG", "/app/ccmemory_log.txt")

_initialized = False


def setupActivityLog():
    """Add activity log file handler to ccmemory logger."""
    global _initialized
    if _initialized:
        return

    logger = logging.getLogger("ccmemory")

    try:
        handler = logging.FileHandler(ACTIVITY_LOG_PATH)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        _initialized = True
    except (OSError, IOError):
        pass


setupActivityLog()
