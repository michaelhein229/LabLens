import pytest

from lablens.indexing.slides import index_slide_record
from lablens.models import SlideTextRecord


class FakeEmbeddingProvider:
    def __init__(self, vectors):
        self.vectors = vectors
        self.document_batches = []

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.document_batches.append(texts.copy())
        return self.vectors

    def embed_query(self, text: str) -> list[float]:
        raise NotImplementedError


def make_slide_record(
    *,
    file_id: str = "file-123",
    presentation_title: str = "PLGA Experiments July",
    slide_number: int = 4,
    slide_id: str = "slide-abc",
    text: str = "Experiment 24 used 2% PVA.",
    modified_time: str = "2024-06-02T12:00:00Z",
    source_url: str = "https://docs.google.com/presentation/d/file-123/edit?usp=sharing",
) -> SlideTextRecord:
    return SlideTextRecord(
        file_id=file_id,
        presentation_title=presentation_title,
        slide_number=slide_number,
        slide_id=slide_id,
        text=text,
        modified_time=modified_time,
        source_url=source_url,
    )


def test_index_slide_record_returns_empty_list_for_empty_input():
    provider = FakeEmbeddingProvider(vectors=[])

    result = index_slide_record([], provider)

    assert result == []
    assert provider.document_batches == []


@pytest.mark.parametrize("blank_text", ["", "   ", "\t\n"])
def test_index_slide_record_skips_blank_slides(blank_text):
    provider = FakeEmbeddingProvider(vectors=[[0.1, 0.2, 0.3]])
    blank_slide = make_slide_record(slide_id="blank-slide", text=blank_text)
    valid_slide = make_slide_record(
        slide_id="valid-slide",
        text="  Experiment   24 used\t2% PVA.  ",
    )

    result = index_slide_record([blank_slide, valid_slide], provider)

    assert len(result) == 1
    assert result[0].source_element_id == "valid-slide"
    assert result[0].text == "Experiment 24 used 2% PVA."
    assert provider.document_batches == [["Experiment 24 used 2% PVA."]]


def test_index_slide_record_returns_empty_list_when_all_slides_are_blank():
    provider = FakeEmbeddingProvider(vectors=[])
    records = [
        make_slide_record(slide_id="slide-1", text=""),
        make_slide_record(slide_id="slide-2", text="   \n\t"),
    ]

    result = index_slide_record(records, provider)

    assert result == []
    assert provider.document_batches == []


def test_index_slide_record_embeds_normalized_text_but_preserves_raw_text():
    provider = FakeEmbeddingProvider(vectors=[[0.4, 0.5, 0.6]])
    record = make_slide_record(
        text="  Experiment   24\r\n\r\n\r\nUsed\t2% PVA.  ",
    )

    result = index_slide_record([record], provider)

    assert len(result) == 1
    assert provider.document_batches == [["Experiment 24\n\nUsed 2% PVA."]]
    assert result[0].text == "Experiment 24\n\nUsed 2% PVA."
    assert result[0].raw_text == "  Experiment   24\r\n\r\n\r\nUsed\t2% PVA.  "


def test_index_slide_record_builds_source_linked_indexed_chunk():
    provider = FakeEmbeddingProvider(vectors=[[0.1, 0.2, 0.3]])
    record = make_slide_record(
        file_id="file-456",
        presentation_title="Release Study May",
        slide_number=12,
        slide_id="slide-def",
        text="High burst release observed.",
        modified_time="2024-07-15T09:30:00Z",
        source_url="https://docs.google.com/presentation/d/file-456/edit#slide=id.old",
    )

    result = index_slide_record([record], provider)

    assert len(result) == 1
    chunk = result[0]
    assert chunk.chunk_id == "file-456:slide:slide-def"
    assert chunk.file_id == "file-456"
    assert chunk.source_type == "google_slides"
    assert chunk.source_title == "Release Study May"
    assert chunk.source_position == 12
    assert chunk.source_element_id == "slide-def"
    assert chunk.raw_text == "High burst release observed."
    assert chunk.text == "High burst release observed."
    assert chunk.vector == [0.1, 0.2, 0.3]
    assert chunk.modified_time == record.modified_time
    assert chunk.source_url == (
        "https://docs.google.com/presentation/d/file-456/edit#slide=id.old"
    )
    assert chunk.citation_url == (
        "https://docs.google.com/presentation/d/file-456/edit#slide=id.slide-def"
    )


def test_index_slide_record_preserves_input_order_when_pairing_vectors():
    provider = FakeEmbeddingProvider(vectors=[[0.1], [0.2]])
    first = make_slide_record(slide_number=1, slide_id="slide-one", text="First slide")
    second = make_slide_record(slide_number=2, slide_id="slide-two", text="Second slide")

    result = index_slide_record([first, second], provider)

    assert [chunk.source_element_id for chunk in result] == ["slide-one", "slide-two"]
    assert [chunk.vector for chunk in result] == [[0.1], [0.2]]
    assert provider.document_batches == [["First slide", "Second slide"]]


def test_index_slide_record_rejects_embedding_count_mismatch():
    provider = FakeEmbeddingProvider(vectors=[[0.1]])
    records = [
        make_slide_record(slide_id="slide-one", text="First slide"),
        make_slide_record(slide_id="slide-two", text="Second slide"),
    ]

    with pytest.raises(ValueError):
        index_slide_record(records, provider)
