from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import health
from app.core.logging import logger
from app.core.config import settings

app = FastAPI(
    title="DesignForge AI",
    description="AI-powered System Design Interview Mentor",
    version="1.0.0",
)

# CORS - allow frontend origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting DesignForge AI backend...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down DesignForge AI backend...")

@app.get("/")
async def root():
    return {
        "message": "Welcome to DesignForge AI API",
        "docs": "/docs"
    }