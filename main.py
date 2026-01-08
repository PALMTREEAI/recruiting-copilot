from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

# Load environment variables from .env file
load_dotenv()

# Import API routes
from app.api.routes import router as api_router

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the scheduler
scheduler = AsyncIOScheduler()


async def send_daily_digest():
    """Send the daily digest email at 7AM."""
    from app.services.analysis import analyze_pipeline
    from app.services.email import send_digest_email

    try:
        logger.info("Starting daily digest email job...")
        snapshot = await analyze_pipeline()
        result = await send_digest_email(snapshot)
        logger.info(f"Daily digest sent successfully! Email ID: {result.get('id', 'unknown')}")
    except Exception as e:
        logger.error(f"Failed to send daily digest: {str(e)}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - start/stop scheduler."""
    # Schedule the daily digest at 7:00 AM local time
    scheduler.add_job(
        send_daily_digest,
        CronTrigger(hour=7, minute=0),
        id="daily_digest",
        name="Send Daily Recruiting Digest",
        replace_existing=True
    )
    scheduler.start()
    logger.info("Scheduler started - Daily digest will be sent at 7:00 AM")

    yield  # Application runs here

    # Shutdown
    scheduler.shutdown()
    logger.info("Scheduler shut down")


# Create FastAPI application
app = FastAPI(
    title="Recruiting Co-Pilot",
    description="A recruiting assistant for managing your hiring pipeline",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)

# Mount static files for the frontend
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    """Serve the main chat interface."""
    return FileResponse("static/index.html")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "recruiting-copilot"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
