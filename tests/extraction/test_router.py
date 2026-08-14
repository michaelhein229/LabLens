from lablens.extraction.router import classify_drive_file
from lablens.models.models import DriveFileMetadata


def test_router():
    slide = DriveFileMetadata(
        file_id="file_id_123",
        file_name="example.txt",
        mime_type="application/vnd.google-apps.presentation",
        created_time="2024-06-01T12:00:00Z",
        modified_time="2024-06-02T12:00:00Z",
        web_url="https://drive.google.com/file/d/file_id_123/view",
        folder_id="folder_id_456"
        )
    doc = DriveFileMetadata(
        file_id="file_id_123",
        file_name="example.txt",
        mime_type="application/vnd.google-apps.document",
        created_time="2024-06-01T12:00:00Z",
        modified_time="2024-06-02T12:00:00Z",
        web_url="https://drive.google.com/file/d/file_id_123/view",
        folder_id="folder_id_456"
        )
    pdf = DriveFileMetadata(
        file_id="file_id_123",
        file_name="example.txt",
        mime_type="application/pdf",
        created_time="2024-06-01T12:00:00Z",
        modified_time="2024-06-02T12:00:00Z",
        web_url="https://drive.google.com/file/d/file_id_123/view",
        folder_id="folder_id_456"
        )
    folder = DriveFileMetadata(
        file_id="file_id_123",
        file_name="example.txt",
        mime_type="application/vnd.google-apps.folder",
        created_time="2024-06-01T12:00:00Z",
        modified_time="2024-06-02T12:00:00Z",
        web_url="https://drive.google.com/file/d/file_id_123/view",
        folder_id="folder_id_456"
        )
    unknown = DriveFileMetadata(
        file_id="file_id_123",
        file_name="example.txt",
        mime_type="text/plain",
        created_time="2024-06-01T12:00:00Z",
        modified_time="2024-06-02T12:00:00Z",
        web_url="https://drive.google.com/file/d/file_id_123/view",
        folder_id="folder_id_456",
    )
    assert classify_drive_file(unknown) == "unsupported"
    assert classify_drive_file(slide) == "presentation"
    assert classify_drive_file(folder) == "folder"
    assert classify_drive_file(doc) == "document"
    assert classify_drive_file(pdf) == "pdf"