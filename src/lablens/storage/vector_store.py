from typing import Protocol
from lablens.indexing.models import IndexedChunk
from lablens.retrieval.models import SearchResult

class VectorStore(Protocol):
    def upsert(self, chunks: list[IndexedChunk]) -> None:
        ...

    def search(
            self,
            query_vector: list[float],
            top_k: int
    ) -> list[SearchResult]:
        ...
