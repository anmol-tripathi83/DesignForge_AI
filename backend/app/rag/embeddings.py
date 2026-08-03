from google import genai
from google.genai import types
from app.core.config import settings
from app.core.logging import logger

# Initialize the Gemini client with your API key
client = genai.Client(api_key=settings.GEMINI_API_KEY)

async def get_embedding(text: str) -> list[float]:
    """
    Generate an embedding vector for a single text using gemini-embedding-2.
    """
    try:
        response = client.models.embed_content(
            model=settings.GEMINI_EMBEDDING_MODEL,
            contents=text,
            config=types.EmbedContentConfig(
                output_dimensionality=settings.EMBEDDING_DIMENSION
            )
        )
        # The response returns an EmbedContentResponse with an 'embeddings' field
        return response.embeddings[0].values
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        raise

async def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for multiple texts in batch using gemini-embedding-2.
    """
    try:
        response = client.models.embed_content(
            model=settings.GEMINI_EMBEDDING_MODEL,
            contents=texts,
            config=types.EmbedContentConfig(
                output_dimensionality=settings.EMBEDDING_DIMENSION
            )
        )
        # Return list of embedding vectors
        return [emb.values for emb in response.embeddings]
    except Exception as e:
        logger.error(f"Failed to generate batch embeddings: {e}")
        raise