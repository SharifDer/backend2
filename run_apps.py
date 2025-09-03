from app_logger import get_logger, setup_uvicorn_logging  # Initialize logging first
from fastapi_app import app
import threading
import subprocess
import sys
import os

logger = get_logger(__name__)

def start_dash_app():
    """Start the Dash app in a separate process"""
    logger.info("Starting Dash app...")
    print("Starting Dash app...")
    dash_script = os.path.join(os.path.dirname(__file__), "DashApp", "dash_app.py")
    subprocess.run([sys.executable, dash_script])

if __name__ == "__main__":
    logger.info("Starting application launcher...")
    
    # Start Dash app in a separate thread
    dash_thread = threading.Thread(target=start_dash_app, daemon=True)
    dash_thread.start()
    
    logger.info("Starting FastAPI app on localhost:8000")
    
    # Configure uvicorn server
    from uvicorn.config import Config
    from uvicorn.server import Server
    
    config = Config(app, host="localhost", port=8000, log_level="info", access_log=True)
    server = Server(config)
    
    # Setup uvicorn logging to write to our centralized log file
    setup_uvicorn_logging()
    
    # Start the server
    server.run()
