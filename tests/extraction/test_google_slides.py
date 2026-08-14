from datetime import datetime

from lablens.models import SlideTextRecord, DriveFileMetadata
from lablens.extraction.google_slides import extract_text_from_slide, extract_slide_text_records
from unittest.mock import MagicMock
from lablens.extraction.google_slides import extract_google_slides


def test_slide_text_record_preserves_source_metadata():
    record = SlideTextRecord(
        file_id="file-123",
        presentation_title="PLGA Experiments July",
        slide_number=1,
        slide_id="slide-abc",
        text="Experiment 24 showed high burst release.",
        modified_time="2024-06-02T12:00:00Z",
        source_url="https://example.test/slides",
    )

    assert record.file_id == "file-123"
    assert record.presentation_title == "PLGA Experiments July"
    assert record.slide_number == 1
    assert record.slide_id == "slide-abc"
    assert record.text == "Experiment 24 showed high burst release."
    assert isinstance(record.modified_time, datetime)
    assert record.source_url == "https://example.test/slides"

from lablens.extraction.google_slides import extract_text_from_slide


def test_extract_text_from_slide_collects_text_runs():
    fake_slide = {
        "objectId": "slide-abc",
        "pageElements": [
            {
                "objectId": "text-box-1",
                "shape": {
                    "text": {
                        "textElements": [
                            {
                                "textRun": {
                                    "content": "Experiment 24\n",
                                }
                            }
                        ]
                    }
                },
            },
            {
                "objectId": "image-1",
                "image": {
                    "contentUrl": "https://example.test/image.png",
                },
            },
            {
                "objectId": "text-box-2",
                "shape": {
                    "text": {
                        "textElements": [
                            {
                                "textRun": {
                                    "content": "High burst release observed.",
                                }
                            }
                        ]
                    }
                },
            },
        ],
    }

    result = extract_text_from_slide(fake_slide)

    assert result == "Experiment 24\nHigh burst release observed."

def test_extract_text_from_slide_returns_empty_string_when_no_text():
    fake_slide = {
        "objectId": "slide-empty",
        "pageElements": [
            {
                "objectId": "image-1",
                "image": {
                    "contentUrl": "https://example.test/image.png",
                },
            },
            {
                "objectId": "line-1",
                "line": {},
            },
        ],
    }

    result = extract_text_from_slide(fake_slide)

    assert result == ""

def test_extract_slide_text_records_creates_one_record_per_slide():
    file_metadata = DriveFileMetadata(
        file_id="file-123",
        file_name="PLGA Experiments July",
        mime_type="application/vnd.google-apps.presentation",
        created_time="2024-06-01T12:00:00Z",
        modified_time="2024-06-02T12:00:00Z",
        web_url="https://example.test/slides",
        folder_id="folder-456",
    )

    fake_presentation = {
        "presentationId": "file-123",
        "title": "PLGA Experiments July",
        "slides": [
            {
                "objectId": "slide-abc",
                "pageElements": [
                    {
                        "objectId": "text-box-1",
                        "shape": {
                            "text": {
                                "textElements": [
                                    {
                                        "textRun": {
                                            "content": "Experiment 24",
                                        }
                                    }
                                ]
                            }
                        },
                    }
                ],
            },
            {
                "objectId": "slide-def",
                "pageElements": [
                    {
                        "objectId": "text-box-2",
                        "shape": {
                            "text": {
                                "textElements": [
                                    {
                                        "textRun": {
                                            "content": "High burst release observed.",
                                        }
                                    }
                                ]
                            }
                        },
                    }
                ],
            },
        ],
    }

    records = extract_slide_text_records(fake_presentation, file_metadata)

    assert len(records) == 2

    assert records[0].file_id == "file-123"
    assert records[0].presentation_title == "PLGA Experiments July"
    assert records[0].slide_number == 1
    assert records[0].slide_id == "slide-abc"
    assert records[0].text == "Experiment 24"
    assert records[0].modified_time == file_metadata.modified_time
    assert records[0].source_url == "https://example.test/slides"

    assert records[1].file_id == "file-123"
    assert records[1].presentation_title == "PLGA Experiments July"
    assert records[1].slide_number == 2
    assert records[1].slide_id == "slide-def"
    assert records[1].text == "High burst release observed."
    assert records[1].modified_time == file_metadata.modified_time
    assert records[1].source_url == "https://example.test/slides"

def test_extract_slide_text_records_returns_empty_list_for_no_slides():
    file_metadata = DriveFileMetadata(
        file_id="file-123",
        file_name="Empty Presentation",
        mime_type="application/vnd.google-apps.presentation",
        created_time="2024-06-01T12:00:00Z",
        modified_time="2024-06-02T12:00:00Z",
        web_url="https://example.test/slides",
        folder_id="folder-456",
    )

    fake_presentation = {
        "presentationId": "file-123",
        "title": "Empty Presentation",
        "slides": [],
    }

    records = extract_slide_text_records(fake_presentation, file_metadata)

    assert records == []

def test_extract_google_slides_fetches_presentation_and_returns_records():
    file_metadata = DriveFileMetadata(
        file_id="file-123",
        file_name="PLGA Experiments July",
        mime_type="application/vnd.google-apps.presentation",
        created_time="2024-06-01T12:00:00Z",
        modified_time="2024-06-02T12:00:00Z",
        web_url="https://example.test/slides",
        folder_id="folder-456",
    )

    fake_presentation = {
        "presentationId": "file-123",
        "title": "PLGA Experiments July",
        "slides": [
            {
                "objectId": "slide-abc",
                "pageElements": [
                    {
                        "shape": {
                            "text": {
                                "textElements": [
                                    {
                                        "textRun": {
                                            "content": "Experiment 24",
                                        }
                                    }
                                ]
                            }
                        }
                    }
                ],
            }
        ],
    }

    slides_service = MagicMock()
    request = slides_service.presentations.return_value.get.return_value
    request.execute.return_value = fake_presentation

    records = extract_google_slides(slides_service, file_metadata)

    assert len(records) == 1
    assert records[0].file_id == "file-123"
    assert records[0].slide_id == "slide-abc"
    assert records[0].text == "Experiment 24"

    slides_service.presentations.return_value.get.assert_called_once_with(
        presentationId="file-123"
    )