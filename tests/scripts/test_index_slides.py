import sys
from types import SimpleNamespace

import pytest

from scripts import index_slides


@pytest.fixture
def cli_environment(monkeypatch):
    state = SimpleNamespace(
        files=[SimpleNamespace(file_name="Deck A", kind="presentation")],
        extracted_files=[],
        indexed_record_batches=[],
        model_names=[],
        provider_models=[],
        auth_calls=[],
        store_configurations=[],
        upsert_calls=[],
    )
    state.drive_service = object()
    state.slides_service = object()
    state.credentials = object()
    state.provider = object()
    state.chunks = [object(), object()]

    monkeypatch.setenv("LABLENS_DRIVE_FOLDER_ID", "folder-123")
    monkeypatch.setattr(index_slides, "load_dotenv", lambda: None)

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

    class FakeChromaVectorStore:
        def __init__(self, persist_path, collection_name):
            state.store_configurations.append(
                {
                    "persist_path": persist_path,
                    "collection_name": collection_name,
                }
            )

        def upsert(self, chunks):
            state.upsert_calls.append(chunks)

    monkeypatch.setattr(
        index_slides,
        "get_google_credentials",
        fake_get_google_credentials,
    )
    monkeypatch.setattr(index_slides, "build", fake_build)
    monkeypatch.setattr(index_slides, "list_folder_files", fake_list_folder_files)
    monkeypatch.setattr(
        index_slides,
        "classify_drive_file",
        lambda file: file.kind,
    )
    monkeypatch.setattr(
        index_slides,
        "extract_google_slides",
        fake_extract_google_slides,
    )
    monkeypatch.setattr(
        index_slides,
        "SentenceTransformer",
        fake_sentence_transformer,
    )
    monkeypatch.setattr(
        index_slides,
        "SentenceTransformerEmbeddingProvider",
        fake_provider,
    )
    monkeypatch.setattr(
        index_slides,
        "index_slide_record",
        fake_index_slide_record,
    )
    monkeypatch.setattr(
        index_slides,
        "ChromaVectorStore",
        FakeChromaVectorStore,
    )

    return state


def test_main_indexes_every_presentation_into_configured_store(
    monkeypatch,
    capsys,
    cli_environment,
):
    state = cli_environment
    first = SimpleNamespace(file_name="Deck A", kind="presentation")
    unsupported = SimpleNamespace(file_name="Notes", kind="document")
    second = SimpleNamespace(file_name="Deck B", kind="presentation")
    state.files = [first, unsupported, second]
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "index_slides.py",
            "--persist-path",
            "custom/chroma",
            "--collection-name",
            "custom-slides",
        ],
    )

    index_slides.main()

    assert state.extracted_files == [first, second]
    assert state.indexed_record_batches == [
        ["record:Deck A", "record:Deck B"]
    ]
    assert state.model_names == ["all-MiniLM-L6-v2"]
    assert len(state.provider_models) == 1
    assert state.store_configurations == [
        {
            "persist_path": "custom/chroma",
            "collection_name": "custom-slides",
        }
    ]
    assert state.upsert_calls == [state.chunks]

    output = capsys.readouterr().out
    assert "Found 3 files in Drive folder." in output
    assert (
        "Indexed 2 searchable slides from 2 presentations "
        "into custom/chroma."
    ) in output


def test_main_uses_default_chroma_configuration(
    monkeypatch,
    cli_environment,
):
    state = cli_environment
    monkeypatch.setattr(sys, "argv", ["index_slides.py"])

    index_slides.main()

    assert state.store_configurations == [
        {
            "persist_path": "data/chroma",
            "collection_name": "lablens-slides",
        }
    ]


def test_main_returns_before_model_loading_when_no_presentations(
    monkeypatch,
    capsys,
    cli_environment,
):
    state = cli_environment
    state.files = [SimpleNamespace(file_name="Notes", kind="document")]
    monkeypatch.setattr(sys, "argv", ["index_slides.py"])

    index_slides.main()

    assert state.extracted_files == []
    assert state.model_names == []
    assert state.store_configurations == []
    assert state.upsert_calls == []
    assert "No Google Slides presentations found." in capsys.readouterr().out


def test_main_does_not_open_store_when_no_chunks_are_searchable(
    monkeypatch,
    capsys,
    cli_environment,
):
    state = cli_environment
    state.chunks = []
    monkeypatch.setattr(sys, "argv", ["index_slides.py"])

    index_slides.main()

    assert len(state.indexed_record_batches) == 1
    assert state.store_configurations == []
    assert state.upsert_calls == []
    assert "No searchable slide text found." in capsys.readouterr().out


def test_main_rejects_missing_folder_id_before_authentication(
    monkeypatch,
    cli_environment,
):
    state = cli_environment
    monkeypatch.delenv("LABLENS_DRIVE_FOLDER_ID")
    monkeypatch.setattr(sys, "argv", ["index_slides.py"])

    with pytest.raises(
        ValueError,
        match="LABLENS_DRIVE_FOLDER_ID is not configured",
    ):
        index_slides.main()

    assert state.auth_calls == []
    assert state.store_configurations == []
    assert state.upsert_calls == []
