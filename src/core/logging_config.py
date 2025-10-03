"""Logging configuration using Loguru"""
import sys
from loguru import logger
from src.core.config import get_settings


def setup_logging():
    """Configure Loguru logger with colorful formatting"""
    settings = get_settings()

    # Remove default handler
    logger.remove()

    # Add custom handler with formatting
    logger.add(
        sys.stdout,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        level=settings.log_level,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    return logger


# Initialize logger on module import
log = setup_logging()

