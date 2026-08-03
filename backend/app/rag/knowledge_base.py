import uuid
from app.rag.embeddings import get_embeddings_batch
from app.rag.qdrant_client import get_qdrant_client, COLLECTION_NAME
from app.core.logging import logger
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ============== KNOWLEDGE DOCUMENTS ==============
KNOWLEDGE_DOCUMENTS = [
    # CAP Theorem
    """
    CAP Theorem (Brewer's Theorem) states that in a distributed system, you can only guarantee two of the following three properties:
    - Consistency: Every read receives the most recent write or an error.
    - Availability: Every request receives a (non-error) response, without guarantee that it contains the most recent write.
    - Partition Tolerance: The system continues to operate despite network partitions.
    In practice, systems must choose between CP (e.g., HBase, MongoDB) or AP (e.g., Cassandra, DynamoDB) when a partition occurs.
    """,
    
    # Consistent Hashing
    """
    Consistent Hashing is a distributed hashing scheme that minimizes rehashing when nodes are added or removed.
    Key concepts:
    - Hash ring: Nodes and keys are mapped to a circle using a hash function.
    - Virtual nodes: Each physical node is represented by multiple virtual nodes on the ring to distribute load evenly.
    - Lookup: A key is stored on the first node clockwise from the key's position on the ring.
    Used in: DynamoDB, Cassandra, Memcached.
    """,
    
    # Load Balancer
    """
    A Load Balancer distributes incoming network traffic across multiple servers to ensure:
    - High availability: If one server fails, traffic is rerouted.
    - Scalability: New servers can be added to handle more load.
    Common algorithms: Round Robin, Least Connections, IP Hash.
    Types: Hardware (F5), Software (HAProxy, Nginx), DNS-based (AWS ELB).
    """,
    
    # Reverse Proxy
    """
    A Reverse Proxy sits between clients and backend servers, forwarding client requests to the appropriate server.
    Benefits:
    - Load balancing: Distributes traffic across servers.
    - Caching: Stores static content to reduce server load.
    - Security: Hides backend server identities.
    - SSL termination: Handles SSL/TLS encryption.
    Examples: Nginx, HAProxy, Apache HTTP Server.
    """,
    
    # Database Sharding
    """
    Database Sharding is a horizontal partitioning strategy where data is split across multiple database instances.
    Sharding strategies:
    - Range-based: Data partitioned by range of a key (e.g., user_id 1-1000 on shard 1).
    - Hash-based: Data distributed using a hash function for uniform distribution.
    - Directory-based: A lookup service maps keys to shards.
    Benefits: Horizontal scaling, improved query performance.
    Challenges: Cross-shard queries, rebalancing, hotspots.
    """,
    
    # Database Replication
    """
    Database Replication creates copies of data across multiple nodes.
    Types:
    - Master-Slave: Writes go to master, reads can go to slaves.
    - Master-Master: Writes can go to any node, conflict resolution required.
    Benefits:
    - High availability: Failover to replica if master fails.
    - Read scalability: Distributing read queries across replicas.
    - Disaster recovery: Data survives node failures.
    Challenges: Replication lag, conflict resolution.
    """,
    
    # Kafka (Message Queue)
    """
    Apache Kafka is a distributed event streaming platform.
    Key concepts:
    - Producer: Publishes messages to topics.
    - Consumer: Subscribes to topics and processes messages.
    - Broker: Server that stores messages.
    - Partition: Topic is split into partitions for parallel processing.
    - Offset: Unique identifier for each message within a partition.
    Guarantees: At-least-once delivery, ordering within a partition.
    Used for: Real-time data pipelines, event sourcing, log aggregation.
    """,
    
    # CDN (Content Delivery Network)
    """
    A Content Delivery Network (CDN) is a geographically distributed network of proxy servers that delivers content to users based on their geographic location.
    Benefits:
    - Reduced latency: Content served from nearby edge servers.
    - Reduced origin load: Caches content, reducing requests to the origin server.
    - DDoS protection: Absorbs traffic spikes.
    Examples: Cloudflare, Akamai, AWS CloudFront.
    Caching strategies: TTL, cache invalidation via purging or versioning.
    """,
    
    # Rate Limiting
    """
    Rate Limiting controls the amount of incoming traffic to an API or service.
    Algorithms:
    - Token Bucket: Tokens added at a fixed rate, requests consume tokens.
    - Leaky Bucket: Requests processed at a fixed rate, overflow is dropped.
    - Sliding Window: Counts requests in the last N seconds.
    - Fixed Window: Counts requests in a fixed time window (e.g., per minute).
    Strategies: Per-user, per-IP, per-API key.
    Response: HTTP 429 (Too Many Requests) with Retry-After header.
    """,
]

def chunk_documents(documents: list[str], chunk_size: int = 500, chunk_overlap: int = 50) -> list[dict]:
    """
    Split large documents into smaller chunks for embedding.
    Each chunk will be stored with metadata.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ".", " ", ""],
    )
    
    chunks = []
    for idx, doc in enumerate(documents):
        split_texts = text_splitter.split_text(doc)
        for chunk in split_texts:
            chunks.append({
                "id": str(uuid.uuid4()),
                "text": chunk,
                "metadata": {
                    "document_id": idx,
                    "source": f"knowledge_doc_{idx}",
                }
            })
    
    logger.info(f"Created {len(chunks)} chunks from {len(documents)} documents.")
    return chunks

async def index_knowledge_base():
    """
    Index all knowledge documents into Qdrant.
    This should be run once (or when the knowledge base changes).
    """
    client = get_qdrant_client()
    
    # Chunk the documents
    chunks = chunk_documents(KNOWLEDGE_DOCUMENTS)
    
    if not chunks:
        logger.warning("No chunks to index.")
        return
    
    # Generate embeddings in batch using the new SDK
    texts = [chunk["text"] for chunk in chunks]
    embeddings = await get_embeddings_batch(texts)
    
    # Prepare points for Qdrant
    points = []
    for chunk, embedding in zip(chunks, embeddings):
        points.append({
            "id": chunk["id"],
            "vector": embedding,
            "payload": {
                "text": chunk["text"],
                **chunk["metadata"]
            }
        })
    
    # Upload to Qdrant
    try:
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points,
        )
        logger.info(f"Successfully indexed {len(points)} chunks into Qdrant.")
    except Exception as e:
        logger.error(f"Failed to index knowledge base: {e}")
        raise