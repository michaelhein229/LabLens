from typing import Protocol


class EmbeddingProvider(Protocol):
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of documents and return their vector representations."""
        ...

    def embed_query(self, text: str) -> list[float]:
        ...

class SentenceTransformerEmbeddingProvider:
    def __init__(self, model):
        self.model = model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if any(not text.strip() for text in texts):
            raise ValueError("Document text must not be blank")
        return self.model.encode(texts).tolist()

    def embed_query(self, text: str) -> list[float]:
        if not text.strip():
            raise ValueError("Query text must not be blank")
        return self.model.encode([text])[0].tolist()