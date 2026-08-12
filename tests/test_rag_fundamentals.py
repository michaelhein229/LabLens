from scripts.rag_fundamentals import create_chunks, cosine_similarity, add_manual_vectors, CHUNK_VECTORS, retrieve, DOCUMENTS
import pytest


def test_create_chunks():
    chunks = create_chunks(DOCUMENTS)
    assert len(chunks) == 9

def test_chunks_have_nonempty_text():
    chunks = create_chunks(DOCUMENTS)

    assert all(chunk["text"].strip() for chunk in chunks)

def test_chunk_ids_are_unique():
    chunks = create_chunks(DOCUMENTS)
    chunk_ids = [chunk["chunk_id"] for chunk in chunks]

    assert len(chunk_ids) == len(set(chunk_ids))

def test_chunks_preserve_source_metadata():
    chunks = create_chunks(DOCUMENTS)

    assert all(chunk["source"] for chunk in chunks)
    assert all(chunk["experiment_id"] for chunk in chunks)

def test_identical_vectors_have_similarity_one():
    result = cosine_similarity([1, 0], [1, 0])
    assert result == pytest.approx(1.0)

def test_orthogonal_vectors_have_similarity_zero():
    result = cosine_similarity([1, 0], [0, 1])
    assert result == pytest.approx(0.0)

def test_parallel_vectors_have_similarity_one():
    result = cosine_similarity([1, 1], [2, 2])
    assert result == pytest.approx(1.0)

def test_unequal_dimensions_raise_error():
    with pytest.raises(ValueError):
        cosine_similarity([1, 0], [1, 0, 0])

def test_zero_vector_raises_error():
    with pytest.raises(ValueError):
        cosine_similarity([0, 0], [1, 0])

def test_add_manual_vectors_assigns_every_vector():
    chunks = create_chunks(DOCUMENTS)
    vectorized_chunks = add_manual_vectors(chunks, CHUNK_VECTORS)

    assert len(vectorized_chunks) == len(chunks)
    assert all("vector" in chunk for chunk in vectorized_chunks)
    assert all(len(chunk["vector"]) == 4 for chunk in vectorized_chunks)

def test_add_manual_vectors_uses_chunk_id_for_lookup():
    chunks = create_chunks(DOCUMENTS)
    vectorized_chunks = add_manual_vectors(chunks, CHUNK_VECTORS)

    target = next(
        chunk
        for chunk in vectorized_chunks
        if chunk["chunk_id"] == "experiment_17_chunk_2"
    )

    assert target["vector"] == [1.0, 0.0, 0.0, 0.0]

def test_add_manual_vectors_preserves_metadata():
    chunks = create_chunks(DOCUMENTS)
    vectorized_chunks = add_manual_vectors(chunks, CHUNK_VECTORS)

    for original, vectorized in zip(chunks, vectorized_chunks):
        assert vectorized["chunk_id"] == original["chunk_id"]
        assert vectorized["source"] == original["source"]
        assert vectorized["experiment_id"] == original["experiment_id"]
        assert vectorized["text"] == original["text"]

def test_add_manual_vectors_rejects_missing_vector():
    chunks = create_chunks(DOCUMENTS)

    with pytest.raises(KeyError):
        add_manual_vectors(chunks, {})

def test_add_manual_vectors_does_not_modify_original_chunks():
    chunks = create_chunks(DOCUMENTS)

    add_manual_vectors(chunks, CHUNK_VECTORS)

    assert all("vector" not in chunk for chunk in chunks)

def test_retrieve_ranks_burst_release_first():
    vectorized_chunks = add_manual_vectors(
        create_chunks(DOCUMENTS),
        CHUNK_VECTORS,
    )

    results = retrieve(
        query_vector=[1.0, 0.0, 0.0, 0.0],
        chunks=vectorized_chunks,
        top_k=3,
    )

    assert len(results) == 3
    assert results[0]["chunk_id"] == "experiment_17_chunk_2"
    assert results[0]["score"] == pytest.approx(1.0)

def test_retrieve_sorts_scores_descending():
    vectorized_chunks = add_manual_vectors(
            create_chunks(DOCUMENTS),
            CHUNK_VECTORS,
        )
    
    results = retrieve(
        query_vector=[1.0, 0.0, 0.0, 0.0],
        chunks=vectorized_chunks,
        top_k=3,
    )

    scores = [result["score"] for result in results]

    assert scores == sorted(scores, reverse=True)

def test_retrieve_top_k_greater_than_chunks_returns_all():
    vectorized_chunks = add_manual_vectors(
        create_chunks(DOCUMENTS),
        CHUNK_VECTORS,
    )

    results = retrieve(
        query_vector=[1.0, 0.0, 0.0, 0.0],
        chunks=vectorized_chunks,
        top_k=20,
    )

    assert len(results) == len(vectorized_chunks)

def test_retrieve_k_equals_zero_returns_value_error():
    vectorized_chunks = add_manual_vectors(
        create_chunks(DOCUMENTS),
        CHUNK_VECTORS,
    )

    with pytest.raises(ValueError):
        retrieve(
            query_vector=[1.0, 0.0, 0.0, 0.0],
            chunks=vectorized_chunks,
            top_k=0,
        )