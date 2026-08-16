import pytest

from lablens.indexing.models import IndexedChunk
from lablens.retrieval.slides import cosine_similarity, search_indexed_chunks


class FakeEmbeddingProvider:
    def __init__(self, query_vector):
        self.query_vector = query_vector
        self.queries = []
        self.document_batches = []

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.document_batches.append(texts.copy())
        raise AssertionError("Search should not embed documents")

    def embed_query(self, text: str) -> list[float]:
        self.queries.append(text)
        return self.query_vector


def make_indexed_chunk(
    *,
    chunk_id: str,
    text: str,
    vector: list[float],
    source_title: str = "PLGA Experiments July",
    slide_number: int = 1,
    slide_id: str = "slide-abc",
    citation_url: str = "https://docs.google.com/presentation/d/file-123/edit#slide=id.slide-abc",
) -> IndexedChunk:
    return IndexedChunk(
        chunk_id=chunk_id,
        file_id="file-123",
        source_type="google_slides",
        source_title=source_title,
        source_position=slide_number,
        source_element_id=slide_id,
        raw_text=text,
        text=text,
        vector=vector,
        modified_time="2024-06-02T12:00:00Z",
        source_url="https://docs.google.com/presentation/d/file-123/edit",
        citation_url=citation_url,
    )


def test_cosine_similarity_identical_vectors_scores_one():
    result = cosine_similarity([1.0, 0.0], [1.0, 0.0])

    assert result == pytest.approx(1.0)


def test_cosine_similarity_orthogonal_vectors_scores_zero():
    result = cosine_similarity([1.0, 0.0], [0.0, 1.0])

    assert result == pytest.approx(0.0)


def test_cosine_similarity_rejects_unequal_dimensions():
    with pytest.raises(ValueError):
        cosine_similarity([1.0, 0.0], [1.0, 0.0, 0.0])


def test_cosine_similarity_rejects_zero_vectors():
    with pytest.raises(ValueError):
        cosine_similarity([0.0, 0.0], [1.0, 0.0])


def test_search_indexed_chunks_ranks_highest_similarity_first():
    provider = FakeEmbeddingProvider(query_vector=[1.0, 0.0])
    chunks = [
        make_indexed_chunk(
            chunk_id="calibration",
            text="Prepared microscope calibration notes.",
            vector=[0.0, 1.0],
            slide_id="slide-calibration",
        ),
        make_indexed_chunk(
            chunk_id="burst-release",
            text="High burst release observed.",
            vector=[1.0, 0.0],
            slide_id="slide-burst-release",
        ),
        make_indexed_chunk(
            chunk_id="partial-match",
            text="Release profile discussed with stability notes.",
            vector=[1.0, 1.0],
            slide_id="slide-partial-match",
        ),
    ]

    results = search_indexed_chunks(
        query="high burst release",
        chunks=chunks,
        provider=provider,
        top_k=3,
    )

    assert [result.chunk.chunk_id for result in results] == [
        "burst-release",
        "partial-match",
        "calibration",
    ]
    assert [result.score for result in results] == sorted(
        [result.score for result in results],
        reverse=True,
    )


def test_search_indexed_chunks_respects_top_k():
    provider = FakeEmbeddingProvider(query_vector=[1.0, 0.0])
    chunks = [
        make_indexed_chunk(chunk_id="first", text="First", vector=[1.0, 0.0]),
        make_indexed_chunk(chunk_id="second", text="Second", vector=[1.0, 1.0]),
        make_indexed_chunk(chunk_id="third", text="Third", vector=[0.0, 1.0]),
    ]

    results = search_indexed_chunks(
        query="release",
        chunks=chunks,
        provider=provider,
        top_k=2,
    )

    assert len(results) == 2
    assert [result.chunk.chunk_id for result in results] == ["first", "second"]


def test_search_indexed_chunks_returns_empty_list_for_empty_index():
    provider = FakeEmbeddingProvider(query_vector=[1.0, 0.0])

    results = search_indexed_chunks(
        query="high burst release",
        chunks=[],
        provider=provider,
    )

    assert results == []
    assert provider.queries == []
    assert provider.document_batches == []


@pytest.mark.parametrize("top_k", [0, -1])
def test_search_indexed_chunks_rejects_invalid_top_k(top_k):
    provider = FakeEmbeddingProvider(query_vector=[1.0, 0.0])
    chunks = [
        make_indexed_chunk(chunk_id="first", text="First", vector=[1.0, 0.0]),
    ]

    with pytest.raises(ValueError):
        search_indexed_chunks(
            query="release",
            chunks=chunks,
            provider=provider,
            top_k=top_k,
        )

    assert provider.queries == []


def test_search_indexed_chunks_preserves_citation_metadata():
    provider = FakeEmbeddingProvider(query_vector=[1.0, 0.0])
    chunk = make_indexed_chunk(
        chunk_id="burst-release",
        text="High burst release observed.",
        vector=[1.0, 0.0],
        source_title="Release Study May",
        slide_number=12,
        slide_id="slide-def",
        citation_url="https://docs.google.com/presentation/d/file-123/edit#slide=id.slide-def",
    )

    results = search_indexed_chunks(
        query="high burst release",
        chunks=[chunk],
        provider=provider,
    )

    assert results[0].chunk.source_title == "Release Study May"
    assert results[0].chunk.source_position == 12
    assert results[0].chunk.source_element_id == "slide-def"
    assert results[0].chunk.citation_url == (
        "https://docs.google.com/presentation/d/file-123/edit#slide=id.slide-def"
    )


def test_search_indexed_chunks_embeds_query_once_and_never_documents():
    provider = FakeEmbeddingProvider(query_vector=[1.0, 0.0])
    chunks = [
        make_indexed_chunk(chunk_id="first", text="First", vector=[1.0, 0.0]),
        make_indexed_chunk(chunk_id="second", text="Second", vector=[0.0, 1.0]),
    ]

    search_indexed_chunks(
        query="release",
        chunks=chunks,
        provider=provider,
        top_k=2,
    )

    assert provider.queries == ["release"]
    assert provider.document_batches == []

