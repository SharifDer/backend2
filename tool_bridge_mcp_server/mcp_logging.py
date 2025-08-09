# Simplified mcp_logging.py - focused on current session only
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Global state
main_logger = None
current_session_handler = None

def setup_main_logging() -> logging.Logger:
    """Setup main server logging (startup, global events)"""
    global main_logger
    
    if main_logger is not None:
        return main_logger
    
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()
    
    # STDERR Handler
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setFormatter(formatter)
    stderr_handler.setLevel(logging.INFO)
    root_logger.addHandler(stderr_handler)
    
    # Main log file
    logs_dir = Path(__file__).parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    main_log_file = logs_dir / f"mcp_server_{timestamp}.log"
    
    main_file_handler = logging.FileHandler(main_log_file, encoding='utf-8')
    main_file_handler.setFormatter(formatter)
    main_file_handler.setLevel(logging.INFO)
    root_logger.addHandler(main_file_handler)
    
    # Quiet libraries
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    
    main_logger = logging.getLogger("mcp_server")
    main_logger.info(f"🔧 Main logging initialized")
    
    return main_logger

def setup_session_logging(session_id: str, session_dir: Path):
    """Add session-specific logging to the current session directory"""
    global current_session_handler
    
    # Remove previous session handler if exists
    if current_session_handler:
        root_logger = logging.getLogger()
        root_logger.removeHandler(current_session_handler)
        current_session_handler.close()
    
    # Create session log file in the session directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_log_file = session_dir / f"session_{session_id}_{timestamp}.log"
    
    # Session-specific formatter with session ID
    formatter = logging.Formatter(
        f"%(asctime)s - [{session_id}] - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
    )
    
    # Create session file handler
    current_session_handler = logging.FileHandler(session_log_file, encoding='utf-8')
    current_session_handler.setFormatter(formatter)
    current_session_handler.setLevel(logging.INFO)
    
    # Add to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(current_session_handler)
    
    # Log session start
    logger = get_logger()
    logger.info(f"🎯 Session {session_id} logging started")

def end_session_logging(session_id: str):
    """Clean up session logging"""
    global current_session_handler
    
    logger = get_logger()
    logger.info(f"🔚 Session {session_id} logging ended")
    
    if current_session_handler:
        root_logger = logging.getLogger()
        root_logger.removeHandler(current_session_handler)
        current_session_handler.close()
        current_session_handler = None

def get_logger(name: str = "mcp_server") -> logging.Logger:
    """Get logger - simplified version"""
    global main_logger
    if main_logger is None:
        main_logger = setup_main_logging()
    return logging.getLogger(name)

# Initialize
logger = setup_main_logging()