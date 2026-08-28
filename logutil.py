"""Rotating error log for diagnosing problems on the customer's machine.

Unhandled exceptions funnel through ``gui.LoginWindow._error_hook``; this
module gives that hook a place to write full stack traces to so the shop's
computer leaves a trail we can inspect later. The file only grows to a fixed
size (older entries are rotated away).
"""

import logging
from logging.handlers import RotatingFileHandler

from paths import LOG_FILE

_logger = None


def get_logger():
    """Return the app logger, configured once with a rotating file handler."""
    global _logger
    if _logger is not None:
        return _logger

    name = "electronstore"
    _logger = logging.getLogger(name)
    if not _logger.handlers:
        try:
            handler = RotatingFileHandler(
                LOG_FILE, maxBytes=512 * 1024, backupCount=3, encoding="utf-8")
            handler.setFormatter(logging.Formatter(
                "%(asctime)s %(levelname)s %(name)s: %(message)s"))
            _logger.addHandler(handler)
        except OSError:
            # Folder not writable — degrade gracefully, never crash the UI.
            _logger.addHandler(logging.NullHandler())
        _logger.setLevel(logging.ERROR)
        _logger.propagate = False
    return _logger