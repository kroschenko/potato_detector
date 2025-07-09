import logging
from logging.handlers import RotatingFileHandler
import os
from configs import LoggerConfigs


def setup_logging():
    # Create logs directory if it doesn't exist
    log_dir = os.path.join("logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # Create a logger
    logger = logging.getLogger('VideoProcessor')
    logger.setLevel(getattr(logging, LoggerConfigs.LOG_LEVEL))
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_formatter = logging.Formatter(
        '[%(levelname)s] %(message)s'
    )
    
    # Create file handler with rotation
    log_file = os.path.join(log_dir, 'video_processor.log')
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=LoggerConfigs.LOG_FILE_MAX_SIZE,
        backupCount=LoggerConfigs.LOG_BACKUP_COUNT
    )
    file_handler.setFormatter(file_formatter)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Log system information
    logger.info("Logging system initialized")
    logger.debug(f"Log directory: {log_dir}")
    logger.debug(f"Log file: {log_file}")
    logger.debug(f"Log level: {LoggerConfigs.LOG_LEVEL}")
    logger.debug(f"Max log file size: {LoggerConfigs.LOG_FILE_MAX_SIZE} bytes")
    logger.debug(f"Log backup count: {LoggerConfigs.LOG_BACKUP_COUNT}")
    
    return logger


# Initialize logger
logger = setup_logging()
