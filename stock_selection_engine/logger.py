
import logging
import sys
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger
from . import config

def setup_logger(name):
    """Configures and returns a logger with JSON file handler and console handler."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG) # Capture everything at root level, handlers filter

    # Prevent duplicate handlers if called multiple times
    if logger.hasHandlers():
        return logger

    # Console Handler (INFO, Standard Format)
    c_handler = logging.StreamHandler(sys.stdout)
    c_handler.setLevel(config.LOG_LEVEL_CONSOLE)
    c_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    c_handler.setFormatter(c_format)
    logger.addHandler(c_handler)

    # File Handler (DEBUG, JSON Format)
    f_handler = RotatingFileHandler(config.LOG_FILE, maxBytes=10*1024*1024, backupCount=5)
    f_handler.setLevel(config.LOG_LEVEL_FILE)
    f_format = jsonlogger.JsonFormatter('%(asctime)s %(name)s %(levelname)s %(message)s %(ticker)s %(module_name)s')
    f_handler.setFormatter(f_format)
    logger.addHandler(f_handler)

    return logger
