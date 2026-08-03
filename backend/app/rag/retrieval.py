from app.rag.qdrant_client import get_qdrant_client, COLLECTION_NAME
from app.rag.embeddings import get_embedding
from app.core.logging import logger

async def retrieve_relevant_chunks(query: str, top_k: int = 3) -> list[str]:
    """
    Retrieve the top_k most relevant knowledge chunks for a given query.
    Returns a list of text chunks.
    """
    try:
        # Generate embedding for the query using the new SDK
        query_embedding = await get_embedding(query)
        
        # Search in Qdrant using the newer query_points API
        client = get_qdrant_client()
        results = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_embedding,
            limit=top_k,
            with_payload=True,
        )
        
        # Extract text from results
        chunks = [hit.payload["text"] for hit in results.points]
        
        logger.info(f"Retrieved {len(chunks)} chunks for query: '{query[:50]}...'")
        return chunks
        
    except Exception as e:
        logger.error(f"Error retrieving chunks: {e}")
        return []