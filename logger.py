import logging
import os
import sys

# Clean up: remove existing log file
log_file = 'app.log'
if os.path.exists(log_file):
    os.remove(log_file)

# Configure logging with proper encoding handling
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(log_file, mode='w', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ],
    force=True  # This clears any existing handlers
)

# Configure console handler for UTF-8 (mainly for Windows)
for handler in logging.getLogger().handlers:
    if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
        try:
            if hasattr(handler.stream, 'reconfigure'):
                handler.stream.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            # Fallback: if reconfigure fails, logging will still work 
            # but might show replacement characters for unsupported Unicode
            pass

logger = logging.getLogger(__name__)