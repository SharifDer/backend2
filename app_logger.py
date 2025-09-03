import logging
import os
import sys
from typing import Optional

# Flag to ensure setup only runs once
_logging_configured = False

class UvicornAccessFormatter(logging.Formatter):
    """Custom formatter that mimics uvicorn's original access log format"""
    def format(self, record):
        # For access logs, use uvicorn's original format without timestamp prefix
        if record.name == "uvicorn.access":
            # The record.msg contains the formatted message from uvicorn
            return f"INFO:     {record.getMessage()}"
        else:
            # For other logs, use our standard format
            return super().format(record)

def setup_logging(log_file: str = 'app.log', log_level: int = logging.INFO, force_reset: bool = False) -> None:
    """
    Configure centralized logging for the entire application.
    
    Args:
        log_file: Path to the log file
        log_level: Logging level (default: INFO)
        force_reset: Whether to force reset existing configuration
    """
    global _logging_configured
    
    if _logging_configured and not force_reset:
        return
    
    # Close all existing handlers for the log file
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        if isinstance(handler, logging.FileHandler) and handler.baseFilename.endswith(log_file):
            handler.close()
            root_logger.removeHandler(handler)

    # Try to remove the existing log file for a fresh start
    if os.path.exists(log_file):
        try:
            os.remove(log_file)
        except PermissionError:
            print(f"Warning: Could not remove log file '{log_file}' - file is in use")

    # Create file handler with explicit flushing
    file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
    file_handler.setLevel(log_level)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Force immediate flushing for all handlers
    for handler in root_logger.handlers:
        if hasattr(handler, 'flush'):
            handler.flush()
    
    # Configure console handler for UTF-8 (mainly for Windows)
    try:
        if hasattr(console_handler.stream, 'reconfigure'):
            console_handler.stream.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    
    _logging_configured = True
    print(f"Logging configured - all logs will be written to '{log_file}'")

def setup_uvicorn_logging(log_file: str = 'app.log') -> None:
    """
    Configure uvicorn access logging to write to our centralized log file.
    Call this after uvicorn server is configured but before it starts.
    """
    # Get uvicorn's access logger
    access_logger = logging.getLogger("uvicorn.access")
    
    # Create file handler for access logs
    file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    
    # Use our custom formatter
    formatter = UvicornAccessFormatter()
    file_handler.setFormatter(formatter)
    
    # Add our file handler to uvicorn's access logger
    access_logger.addHandler(file_handler)
    
    print(f"Uvicorn access logging configured to write to '{log_file}'")

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a named logger for a module.
    
    Args:
        name: Logger name (typically __name__ from the calling module)
    
    Returns:
        Logger instance for the specified name
    """
    # Ensure logging is configured before creating loggers
    if not _logging_configured:
        setup_logging()
    
    return logging.getLogger(name)

# Auto-configure logging when this module is imported
setup_logging()