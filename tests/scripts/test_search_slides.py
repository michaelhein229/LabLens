import sys
from types import SimpleNamespace

import pytest

from scripts import search_slides


@pytest.fixture
def cli_environment(monkeypatch):
    state = SimpleNamespace(
        model_names=[],
        provider_models=[],
        embedded_queries=[],
        embedded_documents=[],
        store_configurations=[],
        search_calls=[],
    )
    state.query_vector = [0.25, 0.5, 0.75]
    state.results = [
        SimpleNamespace(
            score=0.875,
            chunk=SimpleNamespace(
                source_title="Release Study May",
                source_position=12,
                text="High burst release was observed.",
                citation_url=(
                    "https://example.test/release-study"
                    "#slide=id.slide-12"
                ),
            ),
        )
    ]

    def fake_sentence_transformer(model_name):
        state.model_names.append(model_name)
        return object()

    class FakeEmbeddingProvider:
        def __init__(self, model):
            state.provider_models.append(model)

        def embed_query(self, query):
            state.embedded_queries.append(query)
            return state.query_vector

        def embed_documents(self, documents):
            state.embedded_documents.append(documents)
            raise AssertionError("Search must not embed documents")

    class FakeChromaVectorStore:
        def __init__(self, persist_path, collection_name):
            state.store_configurations.append(
                {
                    "persist_path": persist_path,
                    "collection_name": collection_name,
                }
            )

        def search(self, query_vector, top_k):
            state.search_calls.append(
                {
                    "query_vector": query_vector,
                    "top_k": top_k,
                }
            )
            return state.results

    monkeypatch.setattr(
        search_slides,
        "SentenceTransformer",
        fake_sentence_transformer,
    )
    monkeypatch.setattr(
        search_slides,
        "SentenceTransformerEmbeddingProvider",
        FakeEmbeddingProvider,
    )
    monkeypatch.setattr(
        search_slides,
        "ChromaVectorStore",
        FakeChromaVectorStore,
    )

    return state


def test_main_embeds_query_and_searches_configured_store(
    monkeypatch,
    capsys,
    cli_environment,
):
    state = cli_environment
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "search_slides.py",
            "  high burst release  ",
            "--top-k",
            "3",
            "--persist-path",
            "custom/chroma",
            "--collection-name",
            "custom-slides",
        ],
    )

    search_slides.main()

    assert state.model_names == ["all-MiniLM-L6-v2"]
    assert len(state.provider_models) == 1
    assert state.embedded_queries == ["high burst release"]
    assert state.embedded_documents == []
    assert state.store_configurations == [
        {
            "persist_path": "custom/chroma",
            "collection_name": "custom-slides",
        }
    ]
    assert state.search_calls == [
        {
            "query_vector": state.query_vector,
            "top_k": 3,
        }
    ]

    output = capsys.readouterr().out
    assert "Release Study May - Slide 12" in output
    assert "Score: 0.8750" in output
    assert "High burst release was observed." in output
    assert "https://example.test/release-study#slide=id.slide-12" in output


def test_main_uses_default_chroma_configuration(
    monkeypatch,
    cli_environment,
):
    state = cli_environment
    monkeypatch.setattr(sys, "argv", ["search_slides.py", "release"])

    search_slides.main()

    assert state.store_configurations == [
        {
            "persist_path": "data/chroma",
            "collection_name": "lablens-slides",
        }
    ]
    assert state.search_calls[0]["top_k"] == 5


def test_main_prompts_when_query_argument_is_omitted(
    monkeypatch,
    cli_environment,
):
    state = cli_environment
    monkeypatch.setattr(sys, "argv", ["search_slides.py", "--top-k", "2"])
    monkeypatch.setattr("builtins.input", lambda prompt: "particle size")

    search_slides.main()

    assert state.embedded_queries == ["particle size"]
    assert state.search_calls[0]["top_k"] == 2


def test_main_reports_when_saved_index_returns_no_results(
    monkeypatch,
    capsys,
    cli_environment,
):
    state = cli_environment
    state.results = []
    monkeypatch.setattr(sys, "argv", ["search_slides.py", "release"])

    search_slides.main()

    assert len(state.search_calls) == 1
    assert "No results found." in capsys.readouterr().out


@pytest.mark.parametrize("top_k", ["0", "-1"])
def test_main_rejects_nonpositive_top_k_before_model_or_store_creation(
    monkeypatch,
    cli_environment,
    top_k,
):
    state = cli_environment
    monkeypatch.setattr(
        sys,
        "argv",
        ["search_slides.py", "release", "--top-k", top_k],
    )

    with pytest.raises(ValueError, match="top_k must be greater than zero"):
        search_slides.main()

    assert state.model_names == []
    assert state.store_configurations == []
    assert state.search_calls == []


@pytest.mark.parametrize("query", ["", "   ", "\t\n"])
def test_main_rejects_blank_query_before_model_or_store_creation(
    monkeypatch,
    cli_environment,
    query,
):
    state = cli_environment
    monkeypatch.setattr(sys, "argv", ["search_slides.py", query])

    with pytest.raises(ValueError, match="Query must not be blank"):
        search_slides.main()

    assert state.model_names == []
    assert state.store_configurations == []
    assert state.search_calls == []
