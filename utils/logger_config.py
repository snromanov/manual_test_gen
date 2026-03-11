import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


class LoggerConfig:
    """Centralized logging configuration manager"""

    DEFAULT_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    DEFAULT_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    DEFAULT_LEVEL = logging.INFO

    _configured_loggers = {}

    @staticmethod
    def setup_logger(
        name: str = __name__,
        level: int = None,
        log_file: Optional[str] = None,
        log_format: Optional[str] = None,
        date_format: Optional[str] = None,
        console_output: bool = True,
        file_output: bool = True,
        max_bytes: int = 10485760,
        backup_count: int = 3
    ) -> logging.Logger:

        if name in LoggerConfig._configured_loggers:
            return LoggerConfig._configured_loggers[name]

        logger = logging.getLogger(name)
        logger.setLevel(level or LoggerConfig.DEFAULT_LEVEL)
        logger.handlers.clear()

        formatter = logging.Formatter(
            fmt=log_format or LoggerConfig.DEFAULT_FORMAT,
            datefmt=date_format or LoggerConfig.DEFAULT_DATE_FORMAT
        )

        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        if file_output:
            if log_file is None:
                safe_name = name.replace('.', '_').replace('/', '_')
                log_file = f"{safe_name}.log"

            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = RotatingFileHandler(
                log_path,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        LoggerConfig._configured_loggers[name] = logger
        return logger

    @staticmethod
    def setup_basic_logger(
        name: str = __name__,
        level: int = None
    ) -> logging.Logger:
        return LoggerConfig.setup_logger(
            name=name,
            level=level or LoggerConfig.DEFAULT_LEVEL
        )

    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        if name in LoggerConfig._configured_loggers:
            return LoggerConfig._configured_loggers[name]
        return LoggerConfig.setup_basic_logger(name)


def get_logger(name: str = __name__) -> logging.Logger:
    return LoggerConfig.get_logger(name)
