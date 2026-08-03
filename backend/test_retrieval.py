import asyncio
from app.rag.retrieval import retrieve_relevant_chunks

async def test():
    results = await retrieve_relevant_chunks("What is consistent hashing?", top_k=2)
    for i, chunk in enumerate(results):
        print(f"=== Chunk {i+1} ===\n{chunk}\n")

asyncio.run(test())