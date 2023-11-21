import logging
from os import getenv
from os.path import join, isdir
import tg_logger
from telebot import logger as main_logger

from .util import get_logfile

formatter = logging.Formatter('%(module)s : %(levelname)s : %(asctime)s : %(message)s')

# Set the level for the main logger from asynctelebot module to debug, then determine handler levels individually
main_logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler(get_logfile(), encoding='utf-8')
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)  # <---- DETERMINES WHICH LOG LEVELS ARE OUTPUT TO THE LOG FILE

# Set the level of the existing StreamHandler
for handler in main_logger.handlers:
    if isinstance(handler, logging.StreamHandler):
        handler.setLevel(logging.INFO)  # <---- CHANGE TO DEBUG TO GET TRACEBACKS IN THE CONSOLE

# Add file handler to logger
main_logger.addHandler(file_handler)

# Get telegram logger
telegram_logger = logging.getLogger('telegram')
telegram_logger.setLevel(logging.WARN)
tg_logger.setup(telegram_logger,
                token=getenv("TG_BOT_TOKEN"),
                users=getenv("TG_USERS").split(","))  # Logs to the admin user by default


class CustomLogger:
    def __init__(self, main_log, tg_log):
        self.main_logger = main_log
        self.telegram_logger = tg_log

    def debug(self, msg: str, logger_type: str = None, exc_info=None) -> None:
        if logger_type == "main":
            self.main_logger.debug(msg, exc_info=exc_info)
        elif logger_type == "telegram":
            assert exc_info is None, "exc_info is not supported on telegram logger"
            self.telegram_logger.debug(msg)
        elif logger_type is None:
            self.main_logger.debug(msg, exc_info=exc_info)
            self.telegram_logger.debug(msg)

    def info(self, msg: str, logger_type: str = None, exc_info=None) -> None:
        if logger_type == "main":
            self.main_logger.info(msg, exc_info=exc_info)
        elif logger_type == "telegram":
            assert exc_info is None, "exc_info is not supported on telegram logger"
            self.telegram_logger.info(msg)
        elif logger_type is None:
            self.main_logger.info(msg, exc_info=exc_info)
            self.telegram_logger.info(msg)

    def warn(self, msg: str, logger_type: str = None, exc_info=None) -> None:
        if logger_type == "main":
            self.main_logger.warning(msg, exc_info=exc_info)
        elif logger_type == "telegram":
            assert exc_info is None, "exc_info is not supported on telegram logger"
            self.telegram_logger.warning(msg)
        elif logger_type is None:
            self.main_logger.warning(msg, exc_info=exc_info)
            self.telegram_logger.warning(msg)

    def error(self, msg: str, logger_type: str = None, exc_info=None) -> None:
        if logger_type == "main":
            self.main_logger.error(msg, exc_info=exc_info)
        elif logger_type == "telegram":
            assert exc_info is None, "exc_info is not supported on telegram logger"
            self.telegram_logger.error(msg)
        elif logger_type is None:
            self.main_logger.error(msg, exc_info=exc_info)
            self.telegram_logger.error(msg)

    def critical(self, msg: str, logger_type: str = None, exc_info=None) -> None:
        if logger_type == "main":
            self.main_logger.critical(msg, exc_info=exc_info)
        elif logger_type == "telegram":
            assert exc_info is None, "exc_info is not supported on telegram logger"
            self.telegram_logger.critical(msg)
        elif logger_type is None:
            self.main_logger.critical(msg, exc_info=exc_info)
            self.telegram_logger.critical(msg)


# Creating an instance of the CustomLogger class named 'logger'
logger = CustomLogger(main_logger, telegram_logger)