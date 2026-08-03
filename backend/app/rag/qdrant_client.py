from qdrant_client import QdrantClient, models
from app.core.config import settings
from app.core.logging import logger

# Collection name
COLLECTION_NAME = "system_design_knowledge"
EMBEDDING_SIZE = settings.EMBEDDING_DIMENSION  # Now reads from config (768)

def get_qdrant_client() -> QdrantClient:
    """
    Initialize and return Qdrant client.
    """
    return QdrantClient(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY,
    )

async def ensure_collection_exists():
    """
    Create the collection if it doesn't exist.
    """
    client = get_qdrant_client()
    
    try:
        # Check if collection exists
        collections = client.get_collections()
        collection_names = [c.name for c in collections.collections]
        
        if COLLECTION_NAME not in collection_names:
            logger.info(f"Creating collection: {COLLECTION_NAME}")
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=models.VectorParams(
                    size=EMBEDDING_SIZE,
                    distance=models.Distance.COSINE,
                ),
            )
            logger.info(f"Collection {COLLECTION_NAME} created successfully.")
        else:
            logger.info(f"Collection {COLLECTION_NAME} already exists.")
    except Exception as e:
        logger.error(f"Error ensuring collection exists: {e}")
        raise