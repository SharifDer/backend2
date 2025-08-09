import logging
import os
import sys

# Close all existing handlers for the log file
logger = logging.getLogger()
for handler in logger.handlers[:]:
    if isinstance(handler, logging.FileHandler) and handler.baseFilename.endswith('app.log'):
        handler.close()
        logger.removeHandler(handler)

# Now try to remove the file
log_file = 'app.log'
if os.path.exists(log_file):
    try:
        os.remove(log_file)
    except PermissionError:
        print("Warning: Could not remove log file - file is in use")

# Configure logging with proper encoding handling
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(log_file, mode='w', encoding='utf-8'),
        logging.StreamHandler(sys.stderr)
    ],
    force=True  # This clears any existing handlers
)

# Configure console handler for UTF-8 (mainly for Windows)
for handler in logging.getLogger().handlers:
    if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stderr:
        try:
            if hasattr(handler.stream, 'reconfigure'):
                handler.stream.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            # Fallback: if reconfigure fails, logging will still work 
            # but might show replacement characters for unsupported Unicode
            pass

logger = logging.getLogger(__name__)