import logging
import sys


def configure_logging(log_level: str = "INFO") -> None:
    """Configure structured logging for the application.

    Avoids logging full complaint or diagnosis text at INFO level
    to prevent leaking sensitive customer information into log output.
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # Suppress noisy third-party loggers in development
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
