from pydantic import AwareDatetime, BaseModel


class DriveFileMetadata(BaseModel):
    file_id: str
    file_name: str
    mime_type: str
    created_time: AwareDatetime
    modified_time: AwareDatetime
    web_url: str
    folder_id: str


def list_folder_files(
    service,
    folder_id: str,
) -> list[DriveFileMetadata]:
    """Return metadata for direct children of a Drive folder."""
    query = f"'{folder_id}' in parents and trashed = false"
    request = service.files().list(
        q=query,
        pageSize=100,
        fields="nextPageToken, files(id, name, mimeType, createdTime, modifiedTime, webViewLink)",
    )
    response = request.execute()

    return [normalize_drive_file(file, folder_id) for file in response.get("files", [])]

def normalize_drive_file(
    raw_file: dict,
    folder_id: str,
) -> DriveFileMetadata:
    """Convert raw Drive file metadata to a normalized object."""
    return DriveFileMetadata(
        file_id=raw_file["id"],
        file_name=raw_file["name"],
        mime_type=raw_file["mimeType"],
        created_time=raw_file.get("createdTime"),
        modified_time=raw_file["modifiedTime"],
        web_url=raw_file.get("webViewLink", ""),
        folder_id=folder_id,
    )