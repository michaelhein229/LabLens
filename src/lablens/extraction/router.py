from lablens.models.models import DriveFileMetadata


def classify_drive_file(file: DriveFileMetadata) -> str:
    if file.mime_type == "application/vnd.google-apps.presentation":
        return "presentation"
    elif file.mime_type == "application/vnd.google-apps.document":
        return "document"
    elif file.mime_type == "application/pdf":
        return "pdf"
    elif file.mime_type == "application/vnd.google-apps.folder":
        # Need to implement logic to explore subfolders
        return "folder"
    else:
        return "unsupported"