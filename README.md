# LabLens

LabLens is an educational, source-grounded RAG research assistant for laboratory records stored in Google Drive. It is being built incrementally with plain Python so the ingestion, extraction, indexing, retrieval, and citation layers remain understandable and testable.

## Current status

LabLens is in Milestone 3: Lab Data Extracted.

Working features include:

- Google OAuth with locally stored credentials and tokens excluded from Git
- Paginated discovery of direct children in a configured Drive folder
- Validated Drive metadata and MIME-type routing
- Google Slides API extraction into one `SlideTextRecord` per slide
- Preservation of presentation title, file ID, slide number, slide ID, raw text, modification time, and source URL
- Text normalization that preserves scientific capitalization, punctuation, identifiers, and units
- Stable slide chunk IDs and direct links to exact slides
- A replaceable embedding-provider contract and Sentence Transformer adapter
- Deterministic unit tests using fake Drive, Slides, and embedding-model responses

The slide-to-index assembly pipeline is currently under development. It will connect normalized slide records to vectors and citation metadata in memory before persistent vector storage is introduced.

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
IndexedChunk (in progress)
```

The original extracted text remains unchanged. Normalized text is used for embeddings and retrieval, while raw text and source metadata remain available for provenance and debugging.

## Setup

Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

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
55 passing tests
```

## Project structure

```text
src/lablens/ingestion/     Google authentication and Drive discovery
src/lablens/extraction/    Slides, Docs, PDF extraction, routing, normalization
src/lablens/indexing/      Chunk metadata, embedding providers, index assembly
src/lablens/models/        Shared validated source models
scripts/                   Local learning and integration scripts
tests/                     Deterministic unit tests
```

See `PROJECT.md` for the full learning roadmap and architecture, and `PROGRESS.md` for the active milestone and next task.

## MVP boundaries

- Keep the initial pipeline text-only.
- Treat one Google slide as one chunk until evaluation shows a need for splitting or neighbor expansion.
- Do not add OCR, vision descriptions, multimodal embeddings, agents, or desktop UI before grounded text retrieval works end to end.
- Never commit OAuth credentials, tokens, `.env`, or private laboratory content.
