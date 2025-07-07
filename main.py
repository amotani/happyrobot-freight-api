from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from datetime import datetime
import logging
import os

from src.services import initialize_sample_data
from src.routes import webhook_router, loads_router, carriers_router, dashboard_router
from src.auth import check_security_configuration

# Configure logging for production monitoring and debugging
log_level = getattr(logging, os.getenv("LOG_LEVEL", "WARNING").upper(), logging.WARNING)
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan management
    Handles startup tasks like security validation and data initialization
    """
    # Startup
    logger.info("🚀 Starting HappyRobot API...")
    check_security_configuration()  # Validate API keys and security settings
    await initialize_sample_data()  # Load sample carriers and freight loads
    logger.info("✅ API startup complete")
    yield
    # Shutdown (if needed)


# FastAPI application instance with metadata for API documentation
app = FastAPI(
    title="HappyRobot Inbound Carrier API",
    description="API for handling inbound carrier engagement and load management",
    version="1.0.0",
    lifespan=lifespan
)

# Mount static files for dashboard
app.mount("/static", StaticFiles(directory="static"), name="static")

# CORS middleware configuration for cross-origin requests
# Allows HappyRobot platform to call our webhook endpoints
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",") if os.getenv("CORS_ORIGINS", "*") != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API route modules
# Each router handles specific business domain (carriers, loads, webhooks, dashboard)
app.include_router(webhook_router)  # POST /webhook/carrier-engagement
app.include_router(loads_router)    # GET /loads/for-voice-agent
app.include_router(carriers_router) # GET /verify-carrier/{mc_number}
app.include_router(dashboard_router) # GET /dashboard/analytics, /dashboard/status


# Basic health endpoints for monitoring and status checks
@app.get("/")
async def root():
    """Root endpoint - API status and basic information"""
    return {
        "message": "HappyRobot Inbound Carrier API",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers and monitoring systems"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/dashboard")
async def dashboard():
    """Serve the analytics dashboard"""
    from fastapi.responses import FileResponse
    return FileResponse("static/dashboard/index.html")


# Development server configuration
if __name__ == "__main__":
    import uvicorn
    # Run with auto-reload for development
    debug = os.getenv("DEBUG", "true").lower() == "true"
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    if debug:
        # For local development with auto-reload
        uvicorn.run(
            "main:app",  # Use import string for reload
            host=host, 
            port=port, 
            reload=True
        )
    else:
        # For production without reload
        uvicorn.run(
            app, 
            host=host, 
            port=port, 
            reload=False
        ) 