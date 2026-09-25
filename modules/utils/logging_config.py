"""
Centralized Logging Configuration

Professional logging system with file rotation, formatting, and level control.
"""

import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
from typing import Optional
import sys


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        """Format log record with colors."""
        # Add color to level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
        
        # Format the message
        result = super().format(record)
        
        return result


def setup_logging(
    log_dir: str = "logs",
    log_level: str = "INFO",
    console_level: str = "INFO",
    enable_file_logging: bool = True,
    enable_console_logging: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Setup centralized logging configuration.
    
    Args:
        log_dir: Directory for log files
        log_level: Logging level for file output (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        console_level: Logging level for console output
        enable_file_logging: Enable file logging
        enable_console_logging: Enable console logging
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup log files to keep
        
    Returns:
        Root logger instance
    """
    # Create logs directory
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture all levels
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # File handler with rotation
    if enable_file_logging:
        # Main log file
        log_file = log_path / f"ai_symp_controller_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))
        
        # File formatter (detailed)
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(funcName)s() | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
        
        # Error log file (errors and critical only)
        error_log_file = log_path / f"errors_{datetime.now().strftime('%Y%m%d')}.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        root_logger.addHandler(error_handler)
    
    # Console handler with colors
    if enable_console_logging:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, console_level.upper()))
        
        # Console formatter (simplified)
        console_formatter = ColoredFormatter(
            '%(levelname)-8s | %(name)s | %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    # Log startup message
    root_logger.info("=" * 70)
    root_logger.info("AI-Symp-Controller Logging System Initialized")
    root_logger.info(f"Log Directory: {log_path.absolute()}")
    root_logger.info(f"File Logging: {'Enabled' if enable_file_logging else 'Disabled'}")
    root_logger.info(f"Console Logging: {'Enabled' if enable_console_logging else 'Disabled'}")
    root_logger.info("=" * 70)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_exception(logger: logging.Logger, message: str = "Exception occurred"):
    """
    Log an exception with traceback.
    
    Args:
        logger: Logger instance
        message: Custom message
    """
    logger.error(message, exc_info=True)


def log_performance(logger: logging.Logger, operation: str, duration: float):
    """
    Log performance metrics.
    
    Args:
        logger: Logger instance
        operation: Operation name
        duration: Duration in seconds
    """
    if duration > 1.0:
        logger.warning(f"Performance: {operation} took {duration:.2f}s")
    else:
        logger.debug(f"Performance: {operation} took {duration:.3f}s")


class LogContext:
    """Context manager for logging operation start/end."""
    
    def __init__(self, logger: logging.Logger, operation: str, level: str = "INFO"):
        """
        Initialize log context.
        
        Args:
            logger: Logger instance
            operation: Operation name
            level: Log level (INFO, DEBUG, etc.)
        """
        self.logger = logger
        self.operation = operation
        self.level = getattr(logging, level.upper())
        self.start_time = None
    
    def __enter__(self):
        """Enter context."""
        import time
        self.start_time = time.time()
        self.logger.log(self.level, f"Starting: {self.operation}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context."""
        import time
        duration = time.time() - self.start_time
        
        if exc_type is None:
            self.logger.log(self.level, f"Completed: {self.operation} ({duration:.3f}s)")
        else:
            self.logger.error(
                f"Failed: {self.operation} ({duration:.3f}s) - {exc_type.__name__}: {exc_val}",
                exc_info=(exc_type, exc_val, exc_tb)
            )
        
        return False  # Don't suppress exceptions


# Default logger setup (can be customized)
_default_logger_setup = False


def ensure_logging_setup():
    """Ensure logging is setup (call once at startup)."""
    global _default_logger_setup
    if not _default_logger_setup:
        setup_logging()
        _default_logger_setup = True


# Example usage functions
def demo_logging():
    """Demonstrate logging usage."""
    logger = get_logger(__name__)
    
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    # Context manager usage
    with LogContext(logger, "Sample Operation"):
        import time
        time.sleep(0.1)
        logger.info("Doing some work...")
    
    # Exception logging
    try:
        raise ValueError("Example exception")
    except ValueError:
        log_exception(logger, "Caught an exception")


if __name__ == "__main__":
    # Demo
    setup_logging(console_level="DEBUG")
    demo_logging()

