"""
Execution tracking, log reading and metadata persistence.
Handles all I/O operations for monitoring the sync process.
"""
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

# Constants
DEFAULT_LOG_FILE: str = "tests/logs/test_log.log"
DEFAULT_MAX_LINES: int = 10000


def count_log_records_by_level(log_lines: List[str]) -> Dict[str, int]:
    """Count log records by level from a list of log lines.
    
    Args:
        log_lines: List of log lines to analyze.
        
    Returns:
        Dictionary with counts for each log level (ERROR, WARNING, CRITICAL, INFO, DEBUG).
    """
    counts = {
        "ERROR": 0,
        "WARNING": 0,
        "CRITICAL": 0,
        "INFO": 0,
        "DEBUG": 0
    }
    
    for line in log_lines:
        for level in counts.keys():
            if f"[{level}]" in line:
                counts[level] += 1
                break
    
    return counts


def read_recent_log_lines(
    log_file_path: str = DEFAULT_LOG_FILE,
    max_lines: int = DEFAULT_MAX_LINES
) -> List[str]:
    """Read the most recent lines from a log file.
    
    Args:
        log_file_path: Path to the log file.
        max_lines: Maximum number of lines to read from the end.
        
    Returns:
        List of log lines.
    """
    try:
        with open(log_file_path, 'r') as f:
            lines = f.readlines()
            return lines[-max_lines:] if len(lines) > max_lines else lines
    except Exception as e:
        logger.warning(f"Failed to read log file {log_file_path}: {e}")
        return []


def get_log_summary(
    log_file_path: str = DEFAULT_LOG_FILE,
    max_lines: int = DEFAULT_MAX_LINES
) -> Dict[str, int]:
    """Get a summary of log records by level from the log file.
    
    Args:
        log_file_path: Path to the log file.
        max_lines: Maximum number of lines to read from the end.
        
    Returns:
        Dictionary with counts for each log level.
    """
    log_lines = read_recent_log_lines(log_file_path, max_lines)
    return count_log_records_by_level(log_lines)