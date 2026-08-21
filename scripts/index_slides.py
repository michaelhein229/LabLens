import os
import argparse

from dotenv import load_dotenv
from googleapiclient.discovery import build
from sentence_transformers import SentenceTransformer

from lablens.storage.chroma import ChromaVectorStore
from lablens.extraction.google_slides import extract_google_slides
from lablens.extraction.router import classify_drive_file
from lablens.indexing.embeddings import SentenceTransformerEmbeddingProvider
from lablens.indexing.slides import index_slide_record
from lablens.ingestion.google_auth import get_google_credentials
from lablens.ingestion.google_drive import list_folder_files


def main():
    parser = argparse.ArgumentParser(
        description="Index Google Slides into persistent Chroma storage."
    )
    parser.add_argument(
        "--persist-path",
        default="data/chroma",
    )
    parser.add_argument(
        "--collection-name",
        default="lablens-slides",
    )
    args = parser.parse_args()
    load_dotenv()

    folder_id = os.getenv("LABLENS_DRIVE_FOLDER_ID")
    if not folder_id:
        raise ValueError("LABLENS_DRIVE_FOLDER_ID is not configured")
    # 4. Authenticate with Google
    credentials = get_google_credentials()

    # 5. Build Drive service and Slides service\
    drive_service = build("drive", "v3", credentials=credentials)
    slides_service = build("slides", "v1", credentials=credentials)
    # 6. List files in the folder
    files = list_folder_files(drive_service, folder_id)
    print(f"Found {len(files)} files in Drive folder.")
    # 7. Keep only Google Slides presentations
    presentation_files = [
    file for file in files if classify_drive_file(file) == "presentation"
    ]

    if not presentation_files:
        print("No Google Slides presentations found.")
        return
    
    # 8. Extract SlideTextRecord objects from each presentation
    all_records = []
    for record in presentation_files:
        all_records.extend(extract_google_slides(slides_service, record))
    
    # 9. Create SentenceTransformer model/provider
    model = SentenceTransformer("all-MiniLM-L6-v2")
    provider = SentenceTransformerEmbeddingProvider(model)
    # 10. Index slide records into IndexedChunk objects
    chunks = index_slide_record(all_records, provider)
    if not chunks:
        print("No searchable slide text found.")
        return

    vector_store = ChromaVectorStore(
        persist_path=args.persist_path,
        collection_name=args.collection_name,
    )
    vector_store.upsert(chunks)
    print(
        f"Indexed {len(chunks)} searchable slides from "
        f"{len(presentation_files)} presentations into {args.persist_path}."
    )
    

if __name__ == "__main__":
    main()
