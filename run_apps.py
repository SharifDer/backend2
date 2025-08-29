from fastapi_app import app
import uvicorn
import threading
import subprocess
import sys
import os

def start_dash_app():
    """Start the Dash app in a separate process"""
    dash_script = os.path.join(os.path.dirname(__file__), "DashApp", "dash_app.py")
    subprocess.run([sys.executable, dash_script])

if __name__ == "__main__":
    # Start Dash app in a separate thread
    dash_thread = threading.Thread(target=start_dash_app, daemon=True)
    dash_thread.start()
    
    # Start FastAPI app (this will be the main debug session)
    uvicorn.run(app, host="localhost", port=8000)
