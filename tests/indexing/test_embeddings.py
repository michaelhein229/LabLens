from unittest.mock import MagicMock

import numpy as np
import pytest

from lablens.indexing.embeddings import SentenceTransformerEmbeddingProvider


def test_embed_documents_encodes_batch_and_returns_python_lists():
    model = MagicMock()
    model.encode.return_value = np.array(
        [
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6],
        ]
    )
    provider = SentenceTransformerEmbeddingProvider(model)
    texts = ["Experiment 24 used 2% PVA.", "High burst release observed."]

    result = provider.embed_documents(texts)

    assert result == [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
    assert isinstance(result, list)
    assert all(isinstance(vector, list) for vector in result)
    model.encode.assert_called_once_with(texts)


def test_embed_query_returns_one_python_vector():
    model = MagicMock()
    model.encode.return_value = np.array([[0.7, 0.8, 0.9]])
    provider = SentenceTransformerEmbeddingProvider(model)

    result = provider.embed_query("Which experiment had high burst release?")

    assert result == [0.7, 0.8, 0.9]
    assert isinstance(result, list)
    model.encode.assert_called_once_with(
        ["Which experiment had high burst release?"]
    )


def test_embed_documents_returns_empty_list_without_calling_model():
    model = MagicMock()
    provider = SentenceTransformerEmbeddingProvider(model)

    result = provider.embed_documents([])

    assert result == []
    model.encode.assert_not_called()


@pytest.mark.parametrize("blank_text", ["", "   ", "\t\n"])
def test_embed_documents_rejects_blank_text(blank_text):
    model = MagicMock()
    provider = SentenceTransformerEmbeddingProvider(model)

    with pytest.raises(ValueError, match="Document text must not be blank"):
        provider.embed_documents(["Valid experiment text", blank_text])

    model.encode.assert_not_called()


@pytest.mark.parametrize("blank_query", ["", "   ", "\t\n"])
def test_embed_query_rejects_blank_text(blank_query):
    model = MagicMock()
    provider = SentenceTransformerEmbeddingProvider(model)

    with pytest.raises(ValueError, match="Query text must not be blank"):
        provider.embed_query(blank_query)

    model.encode.assert_not_called()


def test_embed_documents_does_not_modify_input():
    model = MagicMock()
    model.encode.return_value = np.array([[0.1, 0.2], [0.3, 0.4]])
    provider = SentenceTransformerEmbeddingProvider(model)
    texts = ["Experiment 17", "Experiment 24"]
    original_texts = texts.copy()

    provider.embed_documents(texts)

    assert texts == original_texts
