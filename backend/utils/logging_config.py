"""
Logging configuration for the healthcare SOAP note taking bot.
Provides structured logging with different levels and formatters.
"""

import logging
import logging.config
import os
import sys
from datetime import datetime
from typing import Dict, Any
import json


class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'session_id'):
            log_entry['session_id'] = record.session_id
        if hasattr(record, 'operation'):
            log_entry['operation'] = record.operation
        if hasattr(record, 'duration_ms'):
            log_entry['duration_ms'] = record.duration_ms
        
        return json.dumps(log_entry)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging(
    level: str = "INFO",
    log_file: str = None,
    structured: bool = False,
    enable_console: bool = True
) -> None:
    """
    Set up application logging configuration.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (if None, only console logging)
        structured: Whether to use structured JSON logging
        enable_console: Whether to enable console logging
    """
    
    # Create logs directory if it doesn't exist
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
    
    # Logging configuration
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'detailed': {
                'format': '%(asctime)s [%(levelname)s] %(name)s.%(funcName)s:%(lineno)d: %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'colored': {
                '()': ColoredFormatter,
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'structured': {
                '()': StructuredFormatter,
            }
        },
        'handlers': {},
        'root': {
            'level': level,
            'handlers': []
        },
        'loggers': {
            'werkzeug': {
                'level': 'WARNING',
                'handlers': [],
                'propagate': True
            },
            'socketio': {
                'level': 'WARNING',
                'handlers': [],
                'propagate': True
            },
            'engineio': {
                'level': 'WARNING',
                'handlers': [],
                'propagate': True
            }
        }
    }
    
    # Add console handler if enabled
    if enable_console:
        config['handlers']['console'] = {
            'class': 'logging.StreamHandler',
            'level': level,
            'formatter': 'colored' if not structured else 'structured',
            'stream': 'ext://sys.stdout'
        }
        config['root']['handlers'].append('console')
    
    # Add file handler if log_file is specified
    if log_file:
        config['handlers']['file'] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': level,
            'formatter': 'structured' if structured else 'detailed',
            'filename': log_file,
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'encoding': 'utf8'
        }
        config['root']['handlers'].append('file')
    
    # Apply configuration
    logging.config.dictConfig(config)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


class LoggingMixin:
    """Mixin class that provides logging capabilities to any class"""
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class"""
        return get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")
    
    def log_operation(self, operation: str, **kwargs):
        """Log an operation with additional context"""
        extra = {'operation': operation}
        extra.update(kwargs)
        return self.logger.info(f"Operation: {operation}", extra=extra)
    
    def log_error(self, error: Exception, operation: str = None, **kwargs):
        """Log an error with additional context"""
        extra = {}
        if operation:
            extra['operation'] = operation
        extra.update(kwargs)
        
        self.logger.error(
            f"Error in {operation or 'unknown operation'}: {str(error)}",
            exc_info=True,
            extra=extra
        )


def log_performance(func):
    """Decorator to log function performance"""
    import time
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(f"{func.__module__}.{func.__name__}")
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            duration_ms = (time.time() - start_time) * 1000
            
            logger.debug(
                f"Function {func.__name__} completed successfully",
                extra={
                    'operation': func.__name__,
                    'duration_ms': round(duration_ms, 2)
                }
            )
            
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            logger.error(
                f"Function {func.__name__} failed: {str(e)}",
                exc_info=True,
                extra={
                    'operation': func.__name__,
                    'duration_ms': round(duration_ms, 2)
                }
            )
            raise
    
    return wrapper


# Initialize logging with default settings
def init_logging():
    """Initialize logging with environment-based configuration"""
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_file = os.getenv('LOG_FILE')
    structured_logging = os.getenv('STRUCTURED_LOGGING', 'false').lower() == 'true'
    
    setup_logging(
        level=log_level,
        log_file=log_file,
        structured=structured_logging,
        enable_console=True
    ) 