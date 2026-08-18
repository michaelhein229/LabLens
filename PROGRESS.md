# Current Milestone
Milestone 4 - Semantic Search

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
- Defined and validated slide-level records with source metadata
- Implemented pure extraction of text runs from Google Slides page structures
- Implemented Slides API extraction through `presentations().get(...)`
- Verified extraction against a real Google Slides presentation
- Added deterministic Google Slides extraction tests using fake API responses
- Added text normalization that preserves scientific capitalization, punctuation, identifiers, units, and meaningful newlines
- Added stable internal slide chunk IDs based on file ID and slide ID
- Added exact-slide citation URL construction with safe URL-fragment replacement
- Defined a replaceable `EmbeddingProvider` protocol
- Implemented a Sentence Transformer embedding adapter with batch document embedding and query embedding
- Added deterministic embedding-provider tests using a fake model
- Completed the in-memory slide indexing pipeline from `SlideTextRecord` to `IndexedChunk`
- Added deterministic tests for slide indexing, blank-slide filtering, vector-count validation, metadata preservation, and citation preservation
- Added an in-memory cosine-similarity retrieval layer over indexed slide chunks
- Added deterministic retrieval tests for ranking, `top_k`, invalid inputs, query-only embedding, and citation metadata preservation
- Added `scripts/search_slides.py` as a thin CLI semantic search demo over extracted Google Slides
- Created a synthetic native Google Slides test deck in the configured Drive folder for retrieval checks
- Verified the CLI can return ranked, cited slide results for natural-language queries
- Reached a verified baseline of 75 passing tests

# Current Work
- Expand the CLI search path from the first discovered presentation to all Google Slides presentations in the configured Drive folder
- Keep scripts thin: orchestration belongs in scripts, while extraction, indexing, retrieval, and storage logic belong in reusable modules
- Begin planning persistent vector storage so normal searches can load existing embeddings instead of re-indexing every slide each run

# Next
- Search all Google Slides presentations in the configured Drive folder and merge their extracted slide records before indexing
- Add a small `VectorStore` abstraction so retrieval code is not tightly coupled to one database implementation
- Add Chroma as the first local persistent vector database
- Create a sync/index command that extracts slides, embeds changed content, and upserts records into the local vector store
- Create a saved-index search command that embeds only the query and searches the persisted vectors
- Store embedding model and indexing metadata so incompatible vectors are not mixed silently
- Evaluate whether slide-only retrieval needs adjacent-slide context expansion
- After persistent retrieval works, add grounded LLM answer generation over the retrieved evidence
- Keep the initial MVP text-only; defer image counting, OCR, vision descriptions, and multimodal embeddings until slide text retrieval and grounded generation work end to end

# Decisions
- Start with plain Python before RAG frameworks
- Use synthetic lab data during early development
- Keep OAuth client credentials and per-user tokens outside Git
- Configure the source folder by ID so each user can connect a different Drive folder
- Use separate extractors for Slides, Docs, and PDFs that emit a common chunk structure
- Keep shared data models in `lablens.models` so ingestion and extraction can use the same validated types
- Return `"unsupported"` for unknown MIME types instead of raising during discovery
- Treat folder recursion as a later extension; current folder listing supports paginated direct children
- Treat one Google slide as one retrieval chunk for the initial MVP
- Preserve raw extracted text and use normalized text for embedding and retrieval
- Use stable slide chunk IDs based on file ID and slide ID; do not include mutable slide numbers
- Construct exact-slide citation URLs from trusted source metadata rather than asking an LLM to invent them
- Keep embedding providers replaceable behind a shared document/query embedding contract
- Keep format-specific index adapters for Slides, Docs, and PDFs while emitting a shared indexed representation
- Use in-memory cosine similarity as the first exact K-nearest-neighbor retrieval implementation
- Treat `top_k` as the number of nearest chunks to return, not as an LLM setting
- Use a vector database for persistence soon; Chroma is the preferred first implementation because it stores vectors, documents, and metadata together locally
- Continue creating embeddings through LabLens providers and pass explicit vectors into the vector database
- Keep LLM answer generation separate from retrieval; add summarization only after retrieval quality is visible and debuggable
- Delay agent orchestration until there are multiple mature retrieval tools such as semantic search, keyword search, metadata filters, and neighbor expansion
- Defer experiment photo understanding for now: future OCR may extract visible labels/text, and future vision models may create derived image descriptions, but those outputs must remain source-linked and clearly labeled as derived rather than original lab observations
- Generate document embeddings during indexing and persist them locally across runs
- Embed only the new question during normal query execution
- Re-index new or changed files by comparing Drive metadata with local index state
- Keep synchronization separate from queries: begin with an explicit Sync command and show index freshness
- Target a local PySide6 desktop application after the command-line RAG MVP works
- Keep model providers replaceable; defer the LLM/provider choice until grounded retrieval is working
- Use synthetic data until authorization and external-service data policies are confirmed for real lab records
