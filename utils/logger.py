"""
Logging setup for YouTube Blog Automation System
Provides structured logging for debugging and monitoring
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path


def setup_logger(name: str = "youtube_blog_automation", log_level: str = None) -> logging.Logger:
    """
    Set up structured logging for the application
    
    Args:
        name: Logger name
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    
    Returns:
        Configured logger instance
    """
    
    # Get log level from environment or default to INFO
    if log_level is None:
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    # Create logs directory
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    # Configure logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level, logging.INFO))
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Create file handler (detailed logging)
    log_file = log_dir / f'youtube_blog_automation_{datetime.now().strftime("%Y%m%d")}.log'
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    # Create console handler (simplified logging)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level, logging.INFO))
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # Create error file handler (errors only)
    error_file = log_dir / f'errors_{datetime.now().strftime("%Y%m%d")}.log'
    error_handler = logging.FileHandler(error_file)
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    logger.addHandler(error_handler)
    
    logger.info(f"Logger initialized - Level: {log_level}")
    logger.info(f"Log file: {log_file}")
    logger.info(f"Error log: {error_file}")
    
    return logger


def log_execution_time(func):
    """
    Decorator to log function execution time
    
    Usage:
        @log_execution_time
        def my_function():
            pass
    """
    import functools
    import time
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger("youtube_blog_automation")
        start_time = time.time()
        
        logger.debug(f"Starting execution: {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"Completed {func.__name__} in {execution_time:.2f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Failed {func.__name__} after {execution_time:.2f}s: {str(e)}")
            raise
    
    return wrapper


def log_api_call(service: str, endpoint: str = "", status: str = "success", details: str = ""):
    """
    Log API calls for monitoring and debugging
    
    Args:
        service: API service name (youtube, medium, unsplash, etc.)
        endpoint: API endpoint called
        status: success, error, or warning
        details: Additional details about the call
    """
    logger = logging.getLogger("youtube_blog_automation")
    
    log_message = f"API Call - {service.upper()}"
    if endpoint:
        log_message += f" | Endpoint: {endpoint}"
    if details:
        log_message += f" | Details: {details}"
    
    if status == "success":
        logger.info(log_message)
    elif status == "error":
        logger.error(log_message)
    elif status == "warning":
        logger.warning(log_message)
    else:
        logger.debug(log_message)


def log_content_stats(content_type: str, stats: dict):
    """
    Log content statistics for monitoring
    
    Args:
        content_type: Type of content (blog_post, research, etc.)
        stats: Dictionary of statistics
    """
    logger = logging.getLogger("youtube_blog_automation")
    
    stats_str = ", ".join([f"{k}: {v}" for k, v in stats.items()])
    logger.info(f"Content Stats - {content_type.upper()} | {stats_str}")


# Create module-level logger instance
default_logger = setup_logger()