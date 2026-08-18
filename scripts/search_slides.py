import argparse
import os

from dotenv import load_dotenv
from googleapiclient.discovery import build
from sentence_transformers import SentenceTransformer

from lablens.extraction.google_slides import extract_google_slides
from lablens.extraction.router import classify_drive_file
from lablens.indexing.embeddings import SentenceTransformerEmbeddingProvider
from lablens.indexing.slides import index_slide_record
from lablens.ingestion.google_auth import get_google_credentials
from lablens.ingestion.google_drive import list_folder_files
from lablens.retrieval.slides import search_indexed_chunks

def main():
    # 1. Read query from command-line args
    parser = argparse.ArgumentParser(
        description="Search indexed Google Slides with a semantic query."
    )
    parser.add_argument("query", type=str)
    parser.add_argument("--top-k", type=int, default=5) 
    args = parser.parse_args()
    query = args.query  
    top_k = args.top_k
    # 2. Load .env
    load_dotenv()
    # 3. Get LABLENS_DRIVE_FOLDER_ID

    folder_id = os.getenv("LABLENS_DRIVE_FOLDER_ID")
    # 4. Authenticate with Google
    credentials = get_google_credentials()

    # 5. Build Drive service and Slides service\
    drive_service = build("drive", "v3", credentials=credentials)
    slides_service = build("slides", "v1", credentials=credentials)
    # 6. List files in the folder
    files = list_folder_files(drive_service, folder_id)
    print(f"Found {len(files)} files in Drive folder.")
    # 7. Keep only Google Slides presentations
    presentation_file = next(
        (file for file in files if classify_drive_file(file) == "presentation"),
        None,
    )

    if presentation_file is None:
        print("No Google Slides presentations found.")
        return

    print(f"Extracting: {presentation_file.file_name}")
    
    # 8. Extract SlideTextRecord objects from each presentation
    records = extract_google_slides(slides_service, presentation_file)
    
    # 9. Create SentenceTransformer model/provider
    model = SentenceTransformer("all-MiniLM-L6-v2")
    provider = SentenceTransformerEmbeddingProvider(model)
    # 10. Index slide records into IndexedChunk objects
    chunks = index_slide_record(records, provider)
    # 11. Search indexed chunks with the query
    results = search_indexed_chunks(
        query=query,
        chunks=chunks,
        provider=provider,
        top_k=top_k
    )
    # 12. Print ranked results
    for index, result in enumerate(results, start=1):
        chunk = result.chunk
        print(f"\n{index}. {chunk.source_title} - Slide {chunk.source_position}")
        print(f"Score: {result.score:.4f}")
        print(f"Text: {chunk.text[:500]}")
        print(f"Source: {chunk.citation_url}")

if __name__ == "__main__":
    main()