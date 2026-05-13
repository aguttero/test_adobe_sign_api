"""
Pure stateless helper functions for the Adobe Sign dashboard.
No IO, no exceptions, no imports from other app modules.
"""
import uuid
import logging
from datetime import datetime
from typing import Tuple, Callable
from functools import wraps


# Logger for this module (used by helpers)
_logger = logging.getLogger(__name__)


# =============================================================================
# Logging Helpers
# =============================================================================
# Log level rules:
#   DEBUG   — internal function detail (bytes read, rows parsed)
#   INFO    — business milestones (token refreshed, rows inserted, pipeline complete)
#   WARNING — recoverable unexpected condition (empty result, skipped step)
#   ERROR   — caught failure, handled (auth failed, API unreachable)
#   CRITICAL — unrecoverable failure, app cannot continue


def log_debug(logger: logging.Logger, message: str) -> None:
    """Log at DEBUG level - internal function detail."""
    logger.debug(message)


def log_info(logger: logging.Logger, message: str) -> None:
    """Log at INFO level - business milestones."""
    logger.info(message)


def log_warning(logger: logging.Logger, message: str) -> None:
    """Log at WARNING level - recoverable unexpected condition."""
    logger.warning(message)


def log_error(logger: logging.Logger, message: str) -> None:
    """Log at ERROR level - caught failure, handled."""
    logger.error(message)


def log_critical(logger: logging.Logger, message: str) -> None:
    """Log at CRITICAL level - unrecoverable failure."""
    logger.critical(message)


def log_function_call(logger: logging.Logger) -> Callable:
    """Decorator to log function calls at DEBUG level.
    
    Usage:
        @log_function_call(logger)
        def my_function(arg1, arg2):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger.debug(f"Calling {func.__name__}(args={len(args)}, kwargs={list(kwargs.keys())})")
            try:
                result = func(*args, **kwargs)
                logger.debug(f"{func.__name__} completed successfully")
                return result
            except Exception as e:
                logger.debug(f"{func.__name__} raised {type(e).__name__}: {e}")
                raise
        return wrapper
    return decorator


def log_operation_result(logger: logging.Logger, operation: str, count: int, level: str = "info") -> None:
    """Log operation result with appropriate level.
    
    Args:
        logger: Logger instance.
        operation: Description of operation (e.g., "Inserted users").
        count: Number of items affected.
        level: Log level - "debug", "info", "warning", "error".
    """
    message = f"{operation}: {count}"
    if level == "debug":
        logger.debug(message)
    elif level == "info":
        logger.info(message)
    elif level == "warning":
        logger.warning(message)
    elif level == "error":
        logger.error(message)


# =============================================================================
# Pure Helper Functions
# =============================================================================

def generate_run_id() -> str:
    """Generate a unique run ID for this execution.
    
    Returns:
        A unique UUID string.
    """
    return str(uuid.uuid4())


def get_current_timestamp() -> datetime:
    """Get the current datetime.
    
    Returns:
        Current datetime object.
    """
    return datetime.now()


def calculate_elapsed_time(start_time: datetime, end_time: datetime) -> Tuple[int, int, float]:
    """Calculate elapsed time between two timestamps.
    
    Args:
        start_time: Start datetime.
        end_time: End datetime.
        
    Returns:
        Tuple of (hours, minutes, seconds_total).
    """
    delta = end_time - start_time
    total_seconds = delta.total_seconds()
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = total_seconds
    
    return hours, minutes, seconds


def format_elapsed_time(hours: int, minutes: int, seconds: float) -> str:
    """Format elapsed time as a readable string.
    
    Args:
        hours: Number of hours.
        minutes: Number of minutes.
        seconds: Total seconds.
        
    Returns:
        Formatted string like "0h 5m 30.50s".
    """
    return f"{hours}h {minutes}m {seconds:.2f}s"


# Transform date with isoformat to naive SQLlite date
def convert_to_sqlite_date(date_iso: str) -> datetime:
    """Convert ISO date string to SQLite date format.
    
    Args:
        date_iso: ISO format date string (e.g., "2026-03-02T08:23:52-08:00")
        
    Returns:
        Date object.
    """
    dt_obj = datetime.fromisoformat(date_iso)
    date_sqlite = dt_obj.date()
    return date_sqlite


## TEST CODE
# fecha_str = "2026-03-02T08:23:52-08:00"
# fecha_final = convert_to_sqlite_date(fecha_str)
# print(fecha_final)  # Resultado: 2026-03-02
# print(type(fecha_final))  # <class 'datetime.date'>