import os

from dotenv import load_dotenv
from googleapiclient.discovery import build

from lablens.extraction.google_slides import extract_google_slides
from lablens.extraction.router import classify_drive_file
from lablens.ingestion.google_auth import get_google_credentials
from lablens.ingestion.google_drive import list_folder_files

def main():
    load_dotenv()

    folder_id = os.environ["LABLENS_DRIVE_FOLDER_ID"]

    credentials = get_google_credentials()

    drive_service = build("drive", "v3", credentials=credentials)
    slides_service = build("slides", "v1", credentials=credentials)

    files = list_folder_files(drive_service, folder_id)
    print(f"Found {len(files)} files in Drive folder.")

    presentation_file = next(
        file for file in files
        if classify_drive_file(file) == "presentation"
    )

    if presentation_file is None:
        print("No Google Slides presentations found.")
        return
    
    print(f"Extracting: {presentation_file.file_name}")

    records = extract_google_slides(slides_service, presentation_file)
    print(f"Extracted {len(records)} slide records.")

    for record in records:
        print(f"\nSlide {record.slide_number}")
        print(record.text[:500])

if __name__ == "__main__":
    main()