import asyncio
from google import genai
from google.genai import types
from app.core.config import settings
from app.core.logging import logger

# Initialize the Gemini client
client = genai.Client(api_key=settings.GEMINI_API_KEY)

async def get_embedding(text: str) -> list[float]:
    """Generate an embedding vector for a single text."""
    try:
        logger.info(f"Generating embedding for text (length: {len(text)})...")
        response = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(
                None,
                lambda: client.models.embed_content(
                    model=settings.GEMINI_EMBEDDING_MODEL,
                    contents=text,
                    config=types.EmbedContentConfig(
                        output_dimensionality=settings.EMBEDDING_DIMENSION
                    )
                )
            ),
            timeout=15.0
        )
        # Access the embedding values from the response
        return response.embeddings[0].values
    except asyncio.TimeoutError:
        logger.error("Embedding generation timed out after 15 seconds.")
        raise
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        raise

async def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for multiple texts in batch."""
    try:
        logger.info(f"Generating batch embeddings for {len(texts)} texts...")
        response = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(
                None,
                lambda: client.models.embed_content(
                    model=settings.GEMINI_EMBEDDING_MODEL,
                    contents=texts,  # Pass a list of strings for batch
                    config=types.EmbedContentConfig(
                        output_dimensionality=settings.EMBEDDING_DIMENSION
                    )
                )
            ),
            timeout=30.0
        )
        # Return a list of embedding vectors
        return [emb.values for emb in response.embeddings]
    except asyncio.TimeoutError:
        logger.error("Batch embedding timed out after 30 seconds.")
        raise
    except Exception as e:
        logger.error(f"Failed to generate batch embeddings: {e}")
        raise