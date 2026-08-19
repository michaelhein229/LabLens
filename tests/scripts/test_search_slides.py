import sys
from types import SimpleNamespace

import pytest

from scripts import search_slides


@pytest.fixture
def cli_environment(monkeypatch):
    state = SimpleNamespace(
        files=[SimpleNamespace(file_name="Deck A", kind="presentation")],
        extracted_files=[],
        indexed_record_batches=[],
        search_calls=[],
        model_names=[],
        provider_models=[],
        auth_calls=[],
        results=[],
    )
    state.drive_service = object()
    state.slides_service = object()
    state.credentials = object()
    state.provider = object()
    state.chunks = [object()]

    monkeypatch.setenv("LABLENS_DRIVE_FOLDER_ID", "folder-123")
    monkeypatch.setattr(search_slides, "load_dotenv", lambda: None)

    def fake_get_google_credentials():
        state.auth_calls.append(True)
        return state.credentials

    def fake_build(api_name, version, credentials):
        assert credentials is state.credentials
        if api_name == "drive":
            assert version == "v3"
            return state.drive_service
        assert api_name == "slides"
        assert version == "v1"
        return state.slides_service

    def fake_list_folder_files(service, folder_id):
        assert service is state.drive_service
        assert folder_id == "folder-123"
        return state.files

    def fake_extract_google_slides(service, presentation_file):
        assert service is state.slides_service
        state.extracted_files.append(presentation_file)
        return [f"record:{presentation_file.file_name}"]

    def fake_sentence_transformer(model_name):
        state.model_names.append(model_name)
        return object()

    def fake_provider(model):
        state.provider_models.append(model)
        return state.provider

    def fake_index_slide_record(records, provider):
        assert provider is state.provider
        state.indexed_record_batches.append(records.copy())
        return state.chunks

    def fake_search_indexed_chunks(*, query, chunks, provider, top_k):
        state.search_calls.append(
            {
                "query": query,
                "chunks": chunks,
                "provider": provider,
                "top_k": top_k,
            }
        )
        return state.results

    monkeypatch.setattr(
        search_slides,
        "get_google_credentials",
        fake_get_google_credentials,
    )
    monkeypatch.setattr(search_slides, "build", fake_build)
    monkeypatch.setattr(search_slides, "list_folder_files", fake_list_folder_files)
    monkeypatch.setattr(
        search_slides,
        "classify_drive_file",
        lambda file: file.kind,
    )
    monkeypatch.setattr(
        search_slides,
        "extract_google_slides",
        fake_extract_google_slides,
    )
    monkeypatch.setattr(
        search_slides,
        "SentenceTransformer",
        fake_sentence_transformer,
    )
    monkeypatch.setattr(
        search_slides,
        "SentenceTransformerEmbeddingProvider",
        fake_provider,
    )
    monkeypatch.setattr(
        search_slides,
        "index_slide_record",
        fake_index_slide_record,
    )
    monkeypatch.setattr(
        search_slides,
        "search_indexed_chunks",
        fake_search_indexed_chunks,
    )

    return state


def test_main_extracts_and_indexes_every_presentation(
    monkeypatch,
    capsys,
    cli_environment,
):
    state = cli_environment
    first = SimpleNamespace(file_name="Deck A", kind="presentation")
    unsupported = SimpleNamespace(file_name="Notes", kind="document")
    second = SimpleNamespace(file_name="Deck B", kind="presentation")
    state.files = [first, unsupported, second]
    state.results = [
        SimpleNamespace(
            score=0.875,
            chunk=SimpleNamespace(
                source_title="Deck B",
                source_position=4,
                text="High burst release was observed.",
                citation_url="https://example.test/deck-b#slide=id.slide-4",
            ),
        )
    ]
    monkeypatch.setattr(
        sys,
        "argv",
        ["search_slides.py", "high burst release", "--top-k", "3"],
    )

    search_slides.main()

    assert state.extracted_files == [first, second]
    assert state.indexed_record_batches == [
        ["record:Deck A", "record:Deck B"]
    ]
    assert state.search_calls == [
        {
            "query": "high burst release",
            "chunks": state.chunks,
            "provider": state.provider,
            "top_k": 3,
        }
    ]
    assert state.model_names == ["all-MiniLM-L6-v2"]
    assert len(state.provider_models) == 1

    output = capsys.readouterr().out
    assert "Deck B - Slide 4" in output
    assert "Score: 0.8750" in output
    assert "https://example.test/deck-b#slide=id.slide-4" in output


def test_main_returns_before_model_loading_when_no_presentations(
    monkeypatch,
    capsys,
    cli_environment,
):
    state = cli_environment
    state.files = [SimpleNamespace(file_name="Notes", kind="document")]
    monkeypatch.setattr(sys, "argv", ["search_slides.py", "release"])

    search_slides.main()

    assert state.extracted_files == []
    assert state.model_names == []
    assert state.search_calls == []
    assert "No Google Slides presentations found." in capsys.readouterr().out


def test_main_reports_when_presentations_have_no_searchable_text(
    monkeypatch,
    capsys,
    cli_environment,
):
    state = cli_environment
    state.chunks = []
    monkeypatch.setattr(sys, "argv", ["search_slides.py", "release"])

    search_slides.main()

    assert state.search_calls == []
    assert "No searchable slide text found." in capsys.readouterr().out


def test_main_reports_when_search_returns_no_results(
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


def test_main_prompts_when_query_argument_is_omitted(
    monkeypatch,
    cli_environment,
):
    state = cli_environment
    monkeypatch.setattr(sys, "argv", ["search_slides.py", "--top-k", "2"])
    monkeypatch.setattr("builtins.input", lambda prompt: "particle size")

    search_slides.main()

    assert state.search_calls[0]["query"] == "particle size"
    assert state.search_calls[0]["top_k"] == 2


def test_main_rejects_missing_folder_id_before_authentication(
    monkeypatch,
    cli_environment,
):
    state = cli_environment
    monkeypatch.delenv("LABLENS_DRIVE_FOLDER_ID")
    monkeypatch.setattr(sys, "argv", ["search_slides.py", "release"])

    with pytest.raises((SystemExit, ValueError)):
        search_slides.main()

    assert state.auth_calls == []


@pytest.mark.parametrize("top_k", ["0", "-1"])
def test_main_rejects_nonpositive_top_k_before_authentication(
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

    with pytest.raises((SystemExit, ValueError)):
        search_slides.main()

    assert state.auth_calls == []


@pytest.mark.parametrize("query", ["", "   ", "\t\n"])
def test_main_rejects_blank_query_before_authentication(
    monkeypatch,
    cli_environment,
    query,
):
    state = cli_environment
    monkeypatch.setattr(sys, "argv", ["search_slides.py", query])

    with pytest.raises((SystemExit, ValueError)):
        search_slides.main()

    assert state.auth_calls == []
