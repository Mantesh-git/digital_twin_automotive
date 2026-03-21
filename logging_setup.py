# logging_setup.py
"""
Module 1 — Logging Setup
=========================
Covers trainer topics:
- Logging best practices (topic 3.6)
- Custom class (topic 3.4)
- Type hints (topic 3.5)
- DEBUG / INFO / WARNING / ERROR separation
"""

import logging
import os
import sys
from typing import Optional
from config import LOG_FILE_PATH, LOG_LEVEL, LOG_FORMAT, LOG_DATE_FORMAT


# ──────────────────────────────────────────
# Custom Exception (trainer topic 3.6)
# ──────────────────────────────────────────
class LoggerSetupError(Exception):
    """Raised when logger cannot be configured."""
    pass


# ──────────────────────────────────────────
# Logger Class
# ──────────────────────────────────────────
class DigitalTwinLogger:
    """
    Centralized logger for the entire Digital Twin system.

    Single Responsibility: ONLY handles logging setup.
    Every module calls get_logger() to get their own logger.

    Class variable _configured ensures setup runs only ONCE
    even if get_logger() is called 100 times across modules.
    """

    _configured: bool = False  # runs setup only once

    @staticmethod
    def setup() -> None:
        """
        Configure root logger with console + file handlers.

        Two handlers:
        - Console → shows logs in VS Code terminal (real time)
        - File    → saves ALL logs to logs/digital_twin.log

        Raises:
            LoggerSetupError: If log folder cannot be created
        """
        if DigitalTwinLogger._configured:
            return  # already set up — skip

        try:
            # Create logs/ folder if not exists
            os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)

            # Formatter — same format for both handlers
            formatter = logging.Formatter(
                fmt=LOG_FORMAT,
                datefmt=LOG_DATE_FORMAT
            )

            # Root logger
            root_logger = logging.getLogger()
            root_logger.setLevel(
                getattr(logging, LOG_LEVEL.upper(), logging.DEBUG)
            )

            # Remove existing handlers to avoid duplicates
            root_logger.handlers.clear()

            # Handler 1 — Console (terminal output)
            console = logging.StreamHandler(sys.stdout)
            console.setFormatter(formatter)
            console.setLevel(logging.DEBUG)

            # Handler 2 — File (persistent log file)
            file_handler = logging.FileHandler(
                LOG_FILE_PATH, encoding="utf-8"
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(logging.DEBUG)

            root_logger.addHandler(console)
            root_logger.addHandler(file_handler)

            DigitalTwinLogger._configured = True

        except OSError as e:
            raise LoggerSetupError(
                f"Cannot create log directory '{LOG_FILE_PATH}': {e}"
            )


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a named logger for any module.

    Call this at the top of every module:
        from logging_setup import get_logger
        logger = get_logger(__name__)

    Args:
        name: Pass __name__ so logs show which module they came from

    Returns:
        logging.Logger: Ready-to-use logger

    Log levels — when to use each:
        logger.debug()   → row-level details, loop counts
        logger.info()    → normal events: file loaded, DB connected
        logger.warning() → recoverable issues: bad row skipped
        logger.error()   → failures: DB down, file missing
    """
    DigitalTwinLogger.setup()
    return logging.getLogger(name)


# ──────────────────────────────────────────
# Quick test — run directly to verify
# ──────────────────────────────────────────
if __name__ == "__main__":
    logger = get_logger(__name__)

    print("\n🔧 Testing all log levels...\n")

    logger.debug(  "DEBUG   — row 1 processed, loop iteration detail")
    logger.info(   "INFO    — 10000 rows loaded, DB connected successfully")
    logger.warning("WARNING — tool wear 185min approaching threshold 200")
    logger.error(  "ERROR   — DB connection failed, file not found")

    print(f"\n✅ Logger working!")
    print(f"   Logs saved to: {LOG_FILE_PATH}")
    print(f"   Log level: {LOG_LEVEL}")