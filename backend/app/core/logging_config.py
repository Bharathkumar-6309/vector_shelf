"""Logging configuration for the application."""

import logging
import sys
from app.config import settings


def setup_logging() -> None:
    """Configure application logging."""
    
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set specific loggers
    logging.getLogger("uvicorn").setLevel(log_level)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING if not settings.debug else logging.INFO)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured at {settings.log_level} level")
