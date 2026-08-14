from lablens.models import DriveFileMetadata


def list_folder_files(
    service,
    folder_id: str,
) -> list[DriveFileMetadata]:
    """Return metadata for direct children of a Drive folder."""
    query = f"'{folder_id}' in parents and trashed = false"
    page_token = None
    all_files = []
    while True:
        request = service.files().list(
            q=query,
            pageSize=100,
            fields="nextPageToken, files(id, name, mimeType, createdTime, modifiedTime, webViewLink)",
            pageToken = page_token
        )
        response = request.execute()
        all_files.extend(response.get("files", []))

        page_token = response.get("nextPageToken")
        if page_token is None:
            break

    return [normalize_drive_file(file, folder_id) for file in all_files]

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
