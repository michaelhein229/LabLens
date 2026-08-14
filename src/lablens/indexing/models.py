from pydantic import BaseModel

class IndexedChunk(BaseModel):
    chunk_id: str
    file_id: str
    source_type: str
    source_title: str
    source_position: int
    source_element_id: str
    raw_text: str
    text: str
    vector: list[float]
    modified_time: str
    source_url: str
    citation_url: str