from datetime import datetime, timezone

import pytest

from lablens.indexing.models import IndexedChunk
from lablens.storage.chroma import ChromaVectorStore


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


@pytest.fixture
def store(tmp_path):
    return ChromaVectorStore(str(tmp_path / "chroma"))


def test_empty_store_returns_no_results(store):
    assert store.search([1.0, 0.0]) == []


def test_empty_upsert_is_a_no_op(store):
    store.upsert([])

    assert store.search([1.0, 0.0]) == []


def test_upserted_chunks_are_searchable_in_similarity_order(store):
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
    assert results[1].score == pytest.approx(2 ** -0.5)
    assert results[2].score == pytest.approx(0.0)


def test_search_respects_top_k(store):
    store.upsert(
        [
            make_chunk(chunk_id="first", vector=[1.0, 0.0]),
            make_chunk(chunk_id="second", vector=[1.0, 1.0]),
            make_chunk(chunk_id="third", vector=[0.0, 1.0]),
        ]
    )

    results = store.search([1.0, 0.0], top_k=2)

    assert [result.chunk.chunk_id for result in results] == ["first", "second"]


def test_upsert_replaces_an_existing_chunk_id(store):
    store.upsert(
        [
            make_chunk(
                chunk_id="experiment-17",
                vector=[0.0, 1.0],
                text="Original text",
            )
        ]
    )
    store.upsert(
        [
            make_chunk(
                chunk_id="experiment-17",
                vector=[1.0, 0.0],
                text="Updated text",
            )
        ]
    )

    results = store.search([1.0, 0.0])

    assert len(results) == 1
    assert results[0].chunk.text == "Updated text"
    assert results[0].chunk.vector == [1.0, 0.0]


def test_records_persist_when_store_is_reopened(tmp_path):
    persist_path = tmp_path / "chroma"
    first_store = ChromaVectorStore(str(persist_path))
    first_store.upsert(
        [make_chunk(chunk_id="persistent", vector=[1.0, 0.0])]
    )

    reopened_store = ChromaVectorStore(str(persist_path))
    results = reopened_store.search([1.0, 0.0])

    assert [result.chunk.chunk_id for result in results] == ["persistent"]


def test_search_reconstructs_source_metadata(store):
    chunk = make_chunk(
        chunk_id="burst-release",
        vector=[1.0, 0.0],
        source_title="Release Study May",
        slide_number=12,
        slide_id="slide-def",
    )
    store.upsert([chunk])

    restored = store.search([1.0, 0.0])[0].chunk

    assert restored == chunk
    assert restored.modified_time == datetime(
        2026, 8, 19, 12, 0, tzinfo=timezone.utc
    )
    assert restored.citation_url.endswith("#slide=id.slide-def")


@pytest.mark.parametrize("top_k", [0, -1])
def test_search_rejects_nonpositive_top_k(store, top_k):
    with pytest.raises(ValueError, match="top_k must be greater than 0"):
        store.search([1.0, 0.0], top_k=top_k)


def test_search_rejects_query_dimension_mismatch(store):
    store.upsert([make_chunk(chunk_id="first", vector=[1.0, 0.0])])

    with pytest.raises(ValueError, match="Query vector dimension"):
        store.search([1.0, 0.0, 0.0])


def test_upsert_rejects_mixed_dimensions_without_partial_insert(store):
    valid = make_chunk(chunk_id="valid", vector=[1.0, 0.0])
    invalid = make_chunk(chunk_id="invalid", vector=[1.0, 0.0, 0.0])

    with pytest.raises(ValueError, match="Chunk vector dimensions"):
        store.upsert([valid, invalid])

    assert store.search([1.0, 0.0]) == []


def test_rejected_replacement_preserves_the_existing_chunk(store):
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

    with pytest.raises(ValueError, match="Chunk vector dimensions"):
        store.upsert([incompatible_replacement])

    results = store.search([1.0, 0.0])
    assert len(results) == 1
    assert results[0].chunk.text == "Original text"
