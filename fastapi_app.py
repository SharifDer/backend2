import os
import sys
import glob
import time
import asyncio
from fastapi.staticfiles import StaticFiles
import stripe
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from backend_common.background import set_background_tasks
from backend_common.database import Database
from backend_common.auth import firebase_db
from config_factory import CONF
from app_logger import get_logger

# Import routers
from routers.authentication import auth_router
from routers.data_layers import data_layers_router
from routers.catalogs import catalogs_router
from routers.stripe_payments import stripe_router
from routers.analysis_intelligence import analysis_router
from routers.campaign import campaign_router
from routers.plans import plans_router
# TODO: Add stripe secret key

stripe.api_key = CONF.stripe_api_key
logger = get_logger(__name__)
logger.info("FastAPI application module loaded successfully")


app = FastAPI()
logger.info("FastAPI app instance created")

# Include routers
app.include_router(auth_router, tags=["Authentication"])
app.include_router(data_layers_router, tags=["Data & Layers"])
app.include_router(catalogs_router, tags=["Catalogs"])
app.include_router(stripe_router, tags=["Stripe"])
app.include_router(analysis_router, tags=["Analysis & Intelligence"])
app.include_router(campaign_router, prefix="", tags=["Campaign"])
app.include_router(plans_router, prefix="", tags=["Plans"])

# Create static directory and mount static files
os.makedirs("static/plots", exist_ok=True)
os.makedirs("static/reports", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


def cleanup_old_files(max_age_hours: int = 24, static_dir: str = "static"):
    """
    Remove plot and report files older than specified hours
    """
    try:
        # Clean plot files
        plot_pattern = os.path.join(static_dir, "plots", "*.png")
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600

        deleted_count = 0
        for filepath in glob.glob(plot_pattern):
            file_age = current_time - os.path.getctime(filepath)
            if file_age > max_age_seconds:
                os.remove(filepath)
                deleted_count += 1

        # Clean report files (keep for 7 days)
        report_pattern = os.path.join(static_dir, "reports", "*.html")
        report_max_age = max_age_hours * 7 * 3600  # 7 times longer than plots
        
        for filepath in glob.glob(report_pattern):
            file_age = current_time - os.path.getctime(filepath)
            if file_age > report_max_age:
                os.remove(filepath)
                deleted_count += 1

        logger.info(f"Cleaned up {deleted_count} old files")

    except Exception as e:
        logger.error(f"Error during file cleanup: {str(e)}")


# Enable CORS
origins = [CONF.enable_CORS_url]

app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=["*"])

app.add_middleware(
    CORSMiddleware,
    # allow_origins=origins,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def background_tasks_middleware(request, call_next):
    background_tasks = BackgroundTasks()
    set_background_tasks(background_tasks)
    response = await call_next(request)
    response.background = background_tasks
    return response


@app.on_event("startup")
async def startup_event():
    # Re-establish our logging configuration after uvicorn startup
    from app_logger import setup_logging
    setup_logging(force_reset=True)
    logger.info("FastAPI startup - logging re-configured")
    
    await Database.create_pool()
    await firebase_db.initialize_all()
    # Clean up old plots on startup
    cleanup_old_files()
    logger.info("FastAPI startup completed")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("FastAPI shutdown initiated")
    await Database.close_pool()
    # Run cleanup in a thread to not block
    await asyncio.get_event_loop().run_in_executor(None, firebase_db.cleanup)
    # Wait a moment to ensure threads are cleaned up
    await asyncio.sleep(1)
    logger.info("FastAPI shutdown completed")

