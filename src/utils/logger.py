"""
Logging configuration for the ticket management system.
"""

import logging
import sys

from src.config import config


def setup_logging() -> None:
    """
    Configure console logging for AWS Lambda.
    """

    log_level = config.LOG_LEVEL or "INFO"

    # Configure log format
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(
        getattr(logging, log_level.upper(), logging.INFO)
    )

    # Remove existing handlers
    root_logger.handlers = []

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)

    root_logger.addHandler(console_handler)

    logging.info("Logging configured successfully")