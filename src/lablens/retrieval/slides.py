from lablens.indexing.embeddings import EmbeddingProvider
from lablens.indexing.models import IndexedChunk
from lablens.retrieval.models import SearchResult
import math

def search_indexed_chunks(
        query: str,
        chunks: list[IndexedChunk],
        provider: EmbeddingProvider,
        top_k: int = 5,
) -> list[SearchResult]:
    if top_k <= 0:
        raise ValueError("Cannot retrieve zero or negative results")

    if not chunks:
        return []

    query_vector = provider.embed_query(query)

    scored_chunks = []
    for chunk in chunks:
        score = cosine_similarity(chunk.vector, query_vector)
        scored_chunks.append((score, chunk))

    scored_chunks.sort(key=lambda item: item[0], reverse=True)
    return [
        SearchResult(chunk=chunk, score=score) 
        for score, chunk in scored_chunks[:top_k]
        ]

def cosine_similarity(
    vector_a: list[float],
    vector_b: list[float],
) -> float:
    if len(vector_a) != len(vector_b):
        raise ValueError("Vectors must have equal dimensions")

    dot_product = math.sumprod(vector_a, vector_b)
    magnitude_a = math.sqrt(sum(x ** 2 for x in vector_a))
    magnitude_b = math.sqrt(sum(x ** 2 for x in vector_b))

    if magnitude_a == 0 or magnitude_b == 0:
        raise ValueError("Cosine similarity is undefined for zero vectors")

    return dot_product / (magnitude_a * magnitude_b)
