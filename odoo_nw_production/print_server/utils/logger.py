"""
Logging Configuration
Configures logging for the print server.
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
import config


def setup_logger(name: str = 'print_server') -> logging.Logger:
    """
    Setup and configure logger.
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, config.LOG_LEVEL))
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    
    # File handler - detailed logs
    file_handler = logging.FileHandler(config.LOG_FILE, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    # Console handler - simple logs
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    return logger


def log_print_job(logger: logging.Logger, job_info: dict):
    """
    Log print job information.
    
    Args:
        logger: Logger instance
        job_info: Dictionary containing job information
    """
    logger.info(
        f"Print Job | "
        f"ID: {job_info.get('job_id')} | "
        f"Printer: {job_info.get('printer')} | "
        f"Type: {job_info.get('report_type')} | "
        f"Order: {job_info.get('order_id')} | "
        f"Size: {job_info.get('size_kb', 0):.2f} KB"
    )


def log_error(logger: logging.Logger, error_info: dict):
    """
    Log error information.
    
    Args:
        logger: Logger instance
        error_info: Dictionary containing error information
    """
    logger.error(
        f"Print Error | "
        f"Printer: {error_info.get('printer')} | "
        f"Error: {error_info.get('error')} | "
        f"Order: {error_info.get('order_id')}"
    )


# Create default logger instance
logger = setup_logger()
