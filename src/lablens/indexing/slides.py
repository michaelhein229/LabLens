from lablens.models import SlideTextRecord

from lablens.indexing.models import IndexedChunk
from lablens.extraction.text_normalization import normalize_text
from lablens.indexing.slide_metadata import build_slide_chunk_id, build_slide_citation_url
from lablens.indexing.embeddings import EmbeddingProvider


def index_slide_record(
    records: list[SlideTextRecord],
    provider: EmbeddingProvider,
) -> list[IndexedChunk]:
    """
    Indexes a list of SlideTextRecord objects by generating embeddings and creating IndexedChunk objects.

    Args:
        records (list[SlideTextRecord]): A list of SlideTextRecord objects to be indexed.
        provider (EmbeddingProvider): An instance of EmbeddingProvider to generate embeddings.

    Returns:
        list[IndexedChunk]: A list of IndexedChunk objects containing the indexed data.
    """

    if not records:
        return []

    prepared_records = []
    for slide in records:
        normalized = normalize_text(slide.text)
        if normalized:
            prepared_records.append((slide, normalized))

    if not prepared_records:
        return []

    embedded_texts = provider.embed_documents([text for _, text in prepared_records])

    if len(embedded_texts) != len(prepared_records):
        raise ValueError("Vectors no longer same length")

    indexed_chunks = []
    for i in range(len(prepared_records)):
        slide = prepared_records[i][0]
        chunk = IndexedChunk(
            chunk_id=build_slide_chunk_id(slide),
            file_id=slide.file_id,
            source_type="google_slides",
            source_title=slide.presentation_title,
            source_position=slide.slide_number,
            source_element_id=slide.slide_id,
            raw_text=slide.text,
            text=prepared_records[i][1],
            vector=embedded_texts[i],
            modified_time=slide.modified_time,
            source_url=slide.source_url,
            citation_url=build_slide_citation_url(slide)
        )
        indexed_chunks.append(chunk)
    return indexed_chunks