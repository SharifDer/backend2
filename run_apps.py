from fastapi_app import app
import uvicorn

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)
