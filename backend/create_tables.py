# backend/create_tables.py
import asyncio
from app.core.database import engine
from app.core.logging import logger
from app.models.user import User  # <-- Import your model so Base knows about it
from app.core.database import Base

async def create_all_tables():
    """Create all tables defined in models."""
    async with engine.begin() as conn:
        # This will create tables that don't exist
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ Tables created successfully!")

if __name__ == "__main__":
    asyncio.run(create_all_tables())