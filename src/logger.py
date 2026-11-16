"""Logging setup."""
import logging


class Logger:
    """Configure the root logger."""

    def __init__(self, level: bool = False) -> None:
        """Store whether debug mode is on."""
        self.level = level

    def init_logger(self) -> None:
        """Attach a stream handler to the root logger."""
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG if self.level else logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))
        logger.addHandler(handler)
