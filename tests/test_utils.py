"""
Pure stateless helper functions for the Adobe Sign dashboard.
No IO, no exceptions, no imports from other app modules.
"""
import uuid
from datetime import datetime
from typing import Tuple


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