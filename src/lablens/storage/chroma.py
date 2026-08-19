import chromadb
from chromadb.errors import InvalidArgumentError

from lablens.indexing.models import IndexedChunk
from lablens.retrieval.models import SearchResult


class ChromaVectorStore:
    def __init__(
        self,
        persist_path: str,
        collection_name: str = "lablens-slides",
    ):
        self._client = chromadb.PersistentClient(path=persist_path)
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            configuration={"hnsw": {"space": "cosine"}},
            embedding_function=None,
        )

    def upsert(self, chunks: list[IndexedChunk]) -> None:
        if not chunks:
            return

        expected_dimension = len(chunks[0].vector)
        if any(len(chunk.vector) != expected_dimension for chunk in chunks):
            raise ValueError("Chunk vector dimensions must match")

        ids: list[str] = []
        embeddings: list[list[float]] = []
        documents: list[str] = []
        metadatas: list[dict[str, str | int]] = []

        for chunk in chunks:
            ids.append(chunk.chunk_id)
            embeddings.append(chunk.vector)
            documents.append(chunk.text)

            metadatas.append({
                "file_id": chunk.file_id,
                "source_type": chunk.source_type,
                "source_title": chunk.source_title,
                "source_position": chunk.source_position,
                "source_element_id": chunk.source_element_id,
                "raw_text": chunk.raw_text,
                "modified_time": chunk.modified_time.isoformat(),
                "source_url": chunk.source_url,
                "citation_url": chunk.citation_url,
            })

        try:
            self._collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
            )
        except InvalidArgumentError as error:
            raise ValueError(
                "Chunk vector dimensions must match the collection"
            ) from error

    def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
    ) -> list[SearchResult]:
        if top_k <= 0:
            raise ValueError("top_k must be greater than 0")

        try:
            results = self._collection.query(
                query_embeddings=[query_vector],
                n_results=top_k,
                include=[
                    "embeddings",
                    "documents",
                    "metadatas",
                    "distances",
                ],
            )
        except InvalidArgumentError as error:
            raise ValueError(
                "Query vector dimension must match stored chunks"
            ) from error

        search_results: list[SearchResult] = []

        for chunk_id, document, metadata, embedding, distance in zip(
            results["ids"][0],
            results["documents"][0],
            results["metadatas"][0],
            results["embeddings"][0],
            results["distances"][0],
        ):
            chunk = IndexedChunk(
                chunk_id=chunk_id,
                text=document,
                vector=embedding.tolist(),
                **metadata,
            )

            search_results.append(
                SearchResult(chunk=chunk, score=1.0 - distance)
            )

        return search_results
