"""
Logging configuration for AWS Lambda.
"""

import logging
import sys

from src.config import config


def setup_logging() -> None:
    """
    Configure console logging only.
    """

    log_level = config.LOG_LEVEL or "INFO"

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Root logger
    root_logger = logging.getLogger()

    # Clear old handlers
    root_logger.handlers = []

    root_logger.setLevel(
        getattr(logging, log_level.upper(), logging.INFO)
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    root_logger.addHandler(console_handler)

    logging.info("Logging configured successfully")