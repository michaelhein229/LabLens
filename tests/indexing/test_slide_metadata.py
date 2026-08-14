import pytest

from lablens.indexing.slide_metadata import (
    build_slide_chunk_id,
    build_slide_citation_url,
)
from lablens.models import SlideTextRecord


@pytest.fixture
def slide_record() -> SlideTextRecord:
    return SlideTextRecord(
        file_id="file-123",
        presentation_title="PLGA Experiments July",
        slide_number=4,
        slide_id="slide-abc",
        text="Experiment 24 used 2% PVA.",
        modified_time="2024-06-02T12:00:00Z",
        source_url=(
            "https://docs.google.com/presentation/d/file-123/edit?usp=sharing"
        ),
    )


def test_build_slide_chunk_id_uses_expected_format(slide_record):
    assert build_slide_chunk_id(slide_record) == "file-123:slide:slide-abc"


def test_build_slide_chunk_id_is_deterministic(slide_record):
    first_id = build_slide_chunk_id(slide_record)
    second_id = build_slide_chunk_id(slide_record)

    assert first_id == second_id


def test_build_slide_chunk_id_differs_for_different_slides(slide_record):
    other_slide = slide_record.model_copy(
        update={"slide_number": 5, "slide_id": "slide-def"}
    )

    assert build_slide_chunk_id(slide_record) != build_slide_chunk_id(other_slide)


def test_build_slide_citation_url_links_to_exact_slide(slide_record):
    result = build_slide_citation_url(slide_record)

    assert result == (
        "https://docs.google.com/presentation/d/file-123/edit"
        "?usp=sharing#slide=id.slide-abc"
    )


def test_build_slide_citation_url_replaces_existing_fragment(slide_record):
    record_with_fragment = slide_record.model_copy(
        update={
            "source_url": (
                "https://docs.google.com/presentation/d/file-123/edit"
                "#slide=id.old-slide"
            )
        }
    )

    result = build_slide_citation_url(record_with_fragment)

    assert result == (
        "https://docs.google.com/presentation/d/file-123/edit"
        "#slide=id.slide-abc"
    )


def test_slide_metadata_helpers_do_not_modify_record(slide_record):
    original_record = slide_record.model_copy(deep=True)

    build_slide_chunk_id(slide_record)
    build_slide_citation_url(slide_record)

    assert slide_record == original_record
