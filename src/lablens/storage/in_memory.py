from lablens.indexing.models import IndexedChunk
from lablens.retrieval.models import SearchResult
from lablens.retrieval.slides import cosine_similarity


class InMemoryVectorStore:
    def __init__(self):
        self._chunks: dict[str, IndexedChunk] = {}
        self._vector_dimension: int | None = None

    def upsert(self, chunks: list[IndexedChunk]) -> None:
        if not chunks:
            return
        expected_dimension = (
            self._vector_dimension
            if self._vector_dimension is not None
            else len(chunks[0].vector)
        )
        for chunk in chunks:
            if len(chunk.vector) != expected_dimension:
                raise ValueError("Chunk vector dimensions must match")
        for chunk in chunks:
            self._chunks[chunk.chunk_id] = chunk

        self._vector_dimension = expected_dimension

    def search(self, query_vector: list[float], top_k: int = 5) -> list[SearchResult]:
        if top_k <= 0:
            raise ValueError("K must be greater than 0")
        if not self._chunks:
            return []
        if len(query_vector) != self._vector_dimension:
            raise ValueError("Query Vector dimension must match dimensional chunks")
        scored_chunks = []
        for chunk in self._chunks.values():
            score = cosine_similarity(chunk.vector, query_vector)
            scored_chunks.append((score, chunk))

        scored_chunks.sort(key=lambda item: item[0], reverse=True)
        return [
            SearchResult(chunk=chunk, score=score)
            for score, chunk in scored_chunks[:top_k]
            ]
