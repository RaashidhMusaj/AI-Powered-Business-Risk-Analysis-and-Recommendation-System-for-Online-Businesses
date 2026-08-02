import logging
import sys
from app.config.settings import settings


def get_logger(name: str) -> logging.Logger:
    """
    Returns a configured structured logger with category naming.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
        
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False
        
    return logger


# Categorized Logger Instances
api_logger = get_logger("API")
ai_logger = get_logger("AI")
scraper_logger = get_logger("SCRAPER")
db_logger = get_logger("DATABASE")
