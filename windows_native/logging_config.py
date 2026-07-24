from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from .paths import OdysseusPaths


def configure_logging(paths: OdysseusPaths, name: str = "odysseus") -> logging.Logger:
    paths.ensure()
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    log_path = paths.logs / f"{name}.log"
    if not any(isinstance(handler, RotatingFileHandler) and handler.baseFilename == str(log_path) for handler in logger.handlers):
        handler = RotatingFileHandler(log_path, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        logger.addHandler(handler)
    return logger
