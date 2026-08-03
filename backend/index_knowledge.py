import asyncio
from app.rag.qdrant_client import ensure_collection_exists
from app.rag.knowledge_base import index_knowledge_base
from app.core.logging import logger

async def main():
    logger.info("Starting knowledge base indexing...")
    
    # Ensure the collection exists
    await ensure_collection_exists()
    
    # Index the knowledge base
    await index_knowledge_base()
    
    logger.info("Knowledge base indexing complete!")

if __name__ == "__main__":
    asyncio.run(main())