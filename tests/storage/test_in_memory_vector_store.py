import pytest

from lablens.indexing.models import IndexedChunk
from lablens.storage.in_memory import InMemoryVectorStore


def make_chunk(
    *,
    chunk_id: str,
    vector: list[float],
    text: str | None = None,
    source_title: str = "PLGA Experiments",
    slide_number: int = 1,
    slide_id: str | None = None,
) -> IndexedChunk:
    resolved_slide_id = slide_id or f"slide-{chunk_id}"
    resolved_text = text or f"Text for {chunk_id}"
    return IndexedChunk(
        chunk_id=chunk_id,
        file_id="file-123",
        source_type="google_slides",
        source_title=source_title,
        source_position=slide_number,
        source_element_id=resolved_slide_id,
        raw_text=resolved_text,
        text=resolved_text,
        vector=vector,
        modified_time="2026-08-19T12:00:00Z",
        source_url="https://docs.google.com/presentation/d/file-123/edit",
        citation_url=(
            "https://docs.google.com/presentation/d/file-123/edit"
            f"#slide=id.{resolved_slide_id}"
        ),
    )


def test_empty_store_returns_no_results():
    store = InMemoryVectorStore()

    assert store.search([1.0, 0.0]) == []


def test_empty_upsert_is_a_no_op():
    store = InMemoryVectorStore()

    store.upsert([])

    assert store.search([1.0, 0.0]) == []


def test_upserted_chunks_are_searchable_in_similarity_order():
    store = InMemoryVectorStore()
    store.upsert(
        [
            make_chunk(chunk_id="orthogonal", vector=[0.0, 1.0]),
            make_chunk(chunk_id="identical", vector=[1.0, 0.0]),
            make_chunk(chunk_id="partial", vector=[1.0, 1.0]),
        ]
    )

    results = store.search([1.0, 0.0], top_k=3)

    assert [result.chunk.chunk_id for result in results] == [
        "identical",
        "partial",
        "orthogonal",
    ]
    assert [result.score for result in results] == sorted(
        [result.score for result in results],
        reverse=True,
    )
    assert results[0].score == pytest.approx(1.0)


def test_search_respects_top_k():
    store = InMemoryVectorStore()
    store.upsert(
        [
            make_chunk(chunk_id="first", vector=[1.0, 0.0]),
            make_chunk(chunk_id="second", vector=[1.0, 1.0]),
            make_chunk(chunk_id="third", vector=[0.0, 1.0]),
        ]
    )

    results = store.search([1.0, 0.0], top_k=2)

    assert [result.chunk.chunk_id for result in results] == ["first", "second"]


def test_search_defaults_to_five_results():
    store = InMemoryVectorStore()
    store.upsert(
        [
            make_chunk(chunk_id=f"chunk-{index}", vector=[1.0, float(index)])
            for index in range(6)
        ]
    )

    assert len(store.search([1.0, 0.0])) == 5


def test_upsert_replaces_an_existing_chunk_id():
    store = InMemoryVectorStore()
    original = make_chunk(
        chunk_id="experiment-17",
        vector=[0.0, 1.0],
        text="Original text",
    )
    replacement = make_chunk(
        chunk_id="experiment-17",
        vector=[1.0, 0.0],
        text="Updated text",
    )

    store.upsert([original])
    store.upsert([replacement])
    results = store.search([1.0, 0.0])

    assert len(results) == 1
    assert results[0].chunk.text == "Updated text"
    assert results[0].chunk.vector == [1.0, 0.0]


def test_separate_upserts_accumulate_unrelated_chunks():
    store = InMemoryVectorStore()
    first = make_chunk(chunk_id="first", vector=[1.0, 0.0])
    second = make_chunk(chunk_id="second", vector=[0.0, 1.0])

    store.upsert([first])
    store.upsert([second])
    results = store.search([1.0, 0.0], top_k=5)

    assert {result.chunk.chunk_id for result in results} == {"first", "second"}


@pytest.mark.parametrize("top_k", [0, -1])
def test_search_rejects_nonpositive_top_k(top_k):
    store = InMemoryVectorStore()

    with pytest.raises(ValueError):
        store.search([1.0, 0.0], top_k=top_k)


def test_search_rejects_query_dimension_mismatch():
    store = InMemoryVectorStore()
    store.upsert([make_chunk(chunk_id="first", vector=[1.0, 0.0])])

    with pytest.raises(ValueError):
        store.search([1.0, 0.0, 0.0])


def test_upsert_rejects_mixed_dimensions_without_partial_insert():
    store = InMemoryVectorStore()
    valid = make_chunk(chunk_id="valid", vector=[1.0, 0.0])
    invalid = make_chunk(chunk_id="invalid", vector=[1.0, 0.0, 0.0])

    with pytest.raises(ValueError):
        store.upsert([valid, invalid])

    assert store.search([1.0, 0.0]) == []


def test_rejected_replacement_preserves_the_existing_chunk():
    store = InMemoryVectorStore()
    original = make_chunk(
        chunk_id="experiment-17",
        vector=[1.0, 0.0],
        text="Original text",
    )
    incompatible_replacement = make_chunk(
        chunk_id="experiment-17",
        vector=[1.0, 0.0, 0.0],
        text="Incompatible replacement",
    )
    store.upsert([original])

    with pytest.raises(ValueError):
        store.upsert([incompatible_replacement])

    results = store.search([1.0, 0.0])
    assert len(results) == 1
    assert results[0].chunk.text == "Original text"


def test_search_preserves_source_and_citation_metadata():
    store = InMemoryVectorStore()
    chunk = make_chunk(
        chunk_id="burst-release",
        vector=[1.0, 0.0],
        source_title="Release Study May",
        slide_number=12,
        slide_id="slide-def",
    )
    store.upsert([chunk])

    result = store.search([1.0, 0.0])[0]

    assert result.chunk.source_title == "Release Study May"
    assert result.chunk.source_position == 12
    assert result.chunk.source_element_id == "slide-def"
    assert result.chunk.citation_url.endswith("#slide=id.slide-def")


def test_upsert_and_search_do_not_mutate_inputs():
    store = InMemoryVectorStore()
    chunk = make_chunk(chunk_id="first", vector=[1.0, 0.0])
    chunks = [chunk]
    query_vector = [1.0, 0.0]
    original_chunks = [item.model_copy(deep=True) for item in chunks]
    original_query = query_vector.copy()

    store.upsert(chunks)
    store.search(query_vector)

    assert chunks == original_chunks
    assert query_vector == original_query
