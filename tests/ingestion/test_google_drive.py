from datetime import datetime


from lablens.ingestion.google_drive import (
    DriveFileMetadata,
    list_folder_files,
    normalize_drive_file,
)

def test_normalize_drive_file():
    raw_file = {
        "id": "file_id_123",
        "name": "example.txt",
        "mimeType": "text/plain",
        "createdTime": "2024-06-01T12:00:00Z",
        "modifiedTime": "2024-06-02T12:00:00Z",
        "webViewLink": "https://drive.google.com/file/d/file_id_123/view",
    }
    folder_id = "folder_id_456"

    normalized_file = normalize_drive_file(raw_file, folder_id)

    assert isinstance(normalized_file, DriveFileMetadata)
    assert normalized_file.file_id == raw_file["id"]
    assert normalized_file.file_name == raw_file["name"]
    assert normalized_file.mime_type == raw_file["mimeType"]
    assert normalized_file.created_time == datetime.fromisoformat(
        raw_file["createdTime"]
    )
    assert normalized_file.modified_time == datetime.fromisoformat(
        raw_file["modifiedTime"]
    )
    assert normalized_file.web_url == raw_file["webViewLink"]
    assert normalized_file.folder_id == folder_id

def test_timestamps_to_dates():
    raw_file = {
        "id": "file_id_123",
        "name": "example.txt",
        "mimeType": "text/plain",
        "createdTime": "2024-06-01T12:00:00Z",
        "modifiedTime": "2024-06-02T12:00:00Z",
        "webViewLink": "https://drive.google.com/file/d/file_id_123/view",
    }
    folder_id = "folder_id_456"

    normalized_file = normalize_drive_file(raw_file, folder_id)

    # Check that the timestamps are converted to datetime objects
    assert isinstance(normalized_file.created_time, datetime)
    assert isinstance(normalized_file.modified_time, datetime)
    assert normalized_file.modified_time.year == 2024
    assert normalized_file.modified_time.month == 6
    assert normalized_file.modified_time.day == 2

def test_timestamps_are_timezone_aware():
    raw_file = {
            "id": "file_id_123",
            "name": "example.txt",
            "mimeType": "text/plain",
            "createdTime": "2024-06-01T12:00:00Z",
            "modifiedTime": "2024-06-02T12:00:00Z",
            "webViewLink": "https://drive.google.com/file/d/file_id_123/view",
        }
    folder_id = "folder_id_456"
    normalized_file = normalize_drive_file(raw_file, folder_id)

    assert normalized_file.created_time.tzinfo is not None
    assert normalized_file.created_time.utcoffset() is not None
    assert normalized_file.modified_time.tzinfo is not None
    assert normalized_file.modified_time.utcoffset() is not None

import pytest
from pydantic import ValidationError


def test_invalid_modified_time_is_rejected():
    raw_file = {
        "id": "file-123",
        "name": "Invalid file",
        "mimeType": "text/plain",
        "createdTime": "2024-06-01T12:00:00Z",
        "modifiedTime": "not-a-timestamp",
        "webViewLink": "https://example.test/file",
    }

    with pytest.raises(ValidationError):
        normalize_drive_file(raw_file, "folder-456")

def test_missing_file_id_is_rejected():
    raw_file = {
        "name": "Missing ID",
        "mimeType": "text/plain",
        "createdTime": "2024-06-01T12:00:00Z",
        "modifiedTime": "2024-06-02T12:00:00Z",
    }

    with pytest.raises(KeyError):
        normalize_drive_file(raw_file, "folder-456")

from unittest.mock import MagicMock

def test_list_folder_files_returns_empty_list():
    service = MagicMock()
    request = service.files.return_value.list.return_value
    request.execute.return_value = {"files": []}

    results = list_folder_files(service, "folder-456")

    assert results == []