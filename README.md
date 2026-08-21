# LabLens

LabLens is an educational, source-grounded RAG research assistant for laboratory records stored in Google Drive. It is being built incrementally with plain Python so the ingestion, extraction, indexing, retrieval, and citation layers remain understandable and testable.

## Current status

LabLens is in Milestone 4: Semantic Search.

Working features include:

- Google OAuth with locally stored credentials and tokens excluded from Git
- Paginated discovery of direct children in a configured Drive folder
- Validated Drive metadata and MIME-type routing
- Google Slides API extraction into one `SlideTextRecord` per slide
- Preservation of presentation title, file ID, slide number, slide ID, raw text, modification time, and source URL
- Text normalization that preserves scientific capitalization, punctuation, identifiers, and units
- Stable slide chunk IDs and direct links to exact slides
- A replaceable embedding-provider contract and Sentence Transformer adapter
- In-memory transformation from `SlideTextRecord` objects to embedded `IndexedChunk` objects
- In-memory cosine-similarity retrieval over indexed slide chunks
- A CLI semantic search script that searches every direct-child Google Slides presentation and prints cited results
- Optional interactive query input with early validation for blank queries, invalid `top_k`, and missing Drive configuration
- A provider-neutral `VectorStore` protocol that accepts explicit document and query vectors
- An in-memory vector-store reference implementation with atomic upsert, stable-ID replacement, dimension validation, and ranked cosine search
- A persistent local `ChromaVectorStore` with cosine search, metadata reconstruction, dimension validation, and stable-ID replacement
- A dedicated indexing CLI that extracts every direct-child Slides presentation, embeds searchable slides, and upserts them into local Chroma storage
- A synthetic PowerPoint test deck that can be imported and converted to native Google Slides for retrieval checks
- Deterministic unit, storage-contract, and CLI orchestration tests using fake Drive, Slides, and embedding-model responses

The document side of persistent retrieval now works: Google Slides can be extracted, embedded, and stored in a local Chroma index that survives application restarts. The existing search CLI still rebuilds an in-memory index, so the current task is to change it to embed only the user's query and search the saved Chroma collection.

## Current pipeline

```text
Google Drive
    ↓
File discovery and MIME routing
    ↓
Google Slides extraction
    ↓
SlideTextRecord (one slide = one MVP chunk)
    ↓
Text normalization
    ↓
Stable chunk ID + exact slide citation
    ↓
Embedding provider
    ↓
IndexedChunk
    ↓
Persistent Chroma collection
    ↓
Query embedding
    ↓
Cosine K-nearest-neighbor retrieval
    ↓
Ranked cited slide results
```

The original extracted text remains unchanged. Normalized text is used for embeddings and retrieval, while raw text and source metadata remain available for provenance and debugging.

## Setup

Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Virtual environments contain platform-specific native packages and should be recreated on each computer rather than copied or synchronized between devices. On Apple Silicon, use `arch -arm64 python3 -m venv .venv` when you need to force a native ARM environment.

Local Google configuration requires:

```text
.env                              LABLENS_DRIVE_FOLDER_ID
secrets/credentials.json          Google OAuth desktop client
secrets/token.json                Generated after local authorization
```

These files are intentionally excluded from Git and may need to be created or reauthorized on each computer.

## Tests

Run the complete suite with the `src` package layout explicitly configured:

```bash
PYTHONPATH=src .venv/bin/python -m pytest -q
```

Current verified baseline:

```text
117 passing tests
```

## CLI indexing

Build or update the persistent local slide index from the project root:

macOS or Linux:

```bash
PYTHONPATH=src .venv/bin/python scripts/index_slides.py
```

Windows PowerShell:

```powershell
$env:PYTHONPATH="src"; .venv\Scripts\python.exe scripts\index_slides.py
```

The command defaults to the `data/chroma` persistence directory and the `lablens-slides` collection. Override them with `--persist-path` and `--collection-name`. It discovers every direct-child Google Slides presentation, extracts and embeds searchable slide text, and upserts the resulting chunks by stable ID. The generated `data/chroma/` database is local data and is excluded from Git.

## CLI search

Run semantic search from the project root with the `src` package path enabled.

macOS or Linux:

```bash
PYTHONPATH=src .venv/bin/python scripts/search_slides.py \
  "high burst release" --top-k 5
```

Windows PowerShell:

```powershell
$env:PYTHONPATH="src"; .venv\Scripts\python.exe scripts\search_slides.py "high burst release" --top-k 5
```

The search CLI accepts a positional query or prompts interactively when one is omitted. It validates inputs before authentication, extracts every direct-child Google Slides presentation, embeds slide text with `all-MiniLM-L6-v2`, searches with cosine similarity, and prints ranked slide results with citation URLs. It still uses the earlier in-memory path and rebuilds the index each run; converting it to query the saved Chroma index is the next task.

## Project structure

```text
src/lablens/ingestion/     Google authentication and Drive discovery
src/lablens/extraction/    Slides, Docs, PDF extraction, routing, normalization
src/lablens/indexing/      Chunk metadata, embedding providers, index assembly
src/lablens/models/        Shared validated source models
src/lablens/retrieval/     Similarity search and retrieval result models
src/lablens/storage/       Vector-store contract, in-memory reference, and Chroma store
scripts/                   Local learning and integration scripts
tests/                     Deterministic unit tests
```

See `PROJECT.md` for the full learning roadmap and architecture, and `PROGRESS.md` for the active milestone and next task.

## MVP boundaries

- Keep the initial pipeline text-only.
- Treat one Google slide as one chunk until evaluation shows a need for splitting or neighbor expansion.
- Do not add OCR, vision descriptions, multimodal embeddings, agents, or desktop UI before text retrieval, persistent indexing, and grounded answers work end to end.
- Never commit OAuth credentials, tokens, `.env`, or private laboratory content.
