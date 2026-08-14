# Current Milestone
Milestone 2 — Drive Connected

# Completed
- Project roadmap defined
- Created paragraph-level chunks from synthetic lab documents
- Preserved source and experiment metadata on chunks
- Added four passing chunk-creation tests
- Implemented cosine similarity with vector validation
- Added cosine similarity tests for identical, orthogonal, and parallel vectors
- Assigned manual feature vectors to all synthetic chunks
- Added tests for vector lookup, metadata preservation, and missing vectors
- Built a deterministic cosine-similarity retriever with top-k ranking
- Tested ranking order, oversized top-k, invalid top-k, and input immutability
- Replaced manual vectors with 384-dimensional Sentence Transformer embeddings
- Retrieved mock lab evidence using a natural-language semantic query
- Completed the RAG fundamentals warmup
- Created the initial `src/lablens/ingestion` package structure
- Installed and verified Google Drive OAuth client dependencies
- Added cross-platform direct dependencies to `requirements.txt`
- Authorized LabLens with Google OAuth and stored a reusable local token
- Loaded the target Drive folder ID from local environment configuration
- Queried the direct children of the configured Drive folder
- Confirmed folder-scoped Drive discovery with the test Slides and Docs files
- Created initial extraction module placeholders for Slides, Docs, PDFs, and routing
- Moved shared Pydantic models into `src/lablens/models`
- Fixed the Pydantic requirement specifier in `requirements.txt`
- Added `pytest.ini` so tests can import the `src` package layout consistently
- Converted raw Google Drive file responses into validated `DriveFileMetadata`
- Added tests for Drive metadata normalization, timestamp parsing, timezone awareness, and invalid metadata rejection
- Added MIME-type routing for Google Slides, Google Docs, PDFs, folders, and unsupported files
- Added Drive API pagination support for folder listing
- Added deterministic pagination tests with a fake Drive service

# Current Work
- Begin Milestone 3 by extracting slide-level text and source metadata from Google Slides

# Next
- Define a `SlideTextRecord` model for extracted slide content
- Implement a pure helper that extracts text runs from a Slides API page structure
- Implement a Google Slides extractor that calls `presentations().get(...)`
- Preserve presentation title, file ID, slide number, slide ID, raw text, modified time, and source URL
- Add deterministic unit tests using fake Slides API responses

# Decisions
- Start with plain Python before RAG frameworks
- Use synthetic lab data during early development
- Keep OAuth client credentials and per-user tokens outside Git
- Configure the source folder by ID so each user can connect a different Drive folder
- Use separate extractors for Slides, Docs, and PDFs that emit a common chunk structure
- Keep shared data models in `lablens.models` so ingestion and extraction can use the same validated types
- Return `"unsupported"` for unknown MIME types instead of raising during discovery
- Treat folder recursion as a later extension; current folder listing supports paginated direct children
- Generate document embeddings during indexing and persist them locally across runs
- Embed only the new question during normal query execution
- Re-index new or changed files by comparing Drive metadata with local index state
- Keep synchronization separate from queries: begin with an explicit Sync command and show index freshness
- Target a local PySide6 desktop application after the command-line RAG MVP works
- Keep model providers replaceable; defer the LLM/provider choice until grounded retrieval is working
- Use synthetic data until authorization and external-service data policies are confirmed for real lab records
