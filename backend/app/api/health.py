from fastapi import APIRouter, status
import logging

router = APIRouter(prefix="/health", tags=["Health"])
logger = logging.getLogger(__name__)

@router.get("/", status_code=status.HTTP_200_OK)
async def health_check():
    logger.info("Health check called")
    return {
        "status": "ok",
        "message": "DesignForge AI backend is running!"
    }