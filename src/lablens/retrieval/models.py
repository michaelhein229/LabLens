from pydantic import BaseModel
from lablens.indexing.models import IndexedChunk


class SearchResult(BaseModel):
    chunk: IndexedChunk
    score: float
