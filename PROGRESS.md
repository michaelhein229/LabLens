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

# Current Work
- Convert raw Google Drive file responses into standardized LabLens metadata

# Next
- Add MIME-type routing for Slides, Docs, PDFs, and folders
- Add Drive API pagination
- Add deterministic tests for folder listing with a fake Drive service
- Extract slide-level text and source metadata from Google Slides

# Decisions
- Start with plain Python before RAG frameworks
- Use synthetic lab data during early development
- Keep OAuth client credentials and per-user tokens outside Git
- Configure the source folder by ID so each user can connect a different Drive folder
- Use separate extractors for Slides, Docs, and PDFs that emit a common chunk structure
- Generate document embeddings during indexing and persist them locally across runs
- Embed only the new question during normal query execution
- Re-index new or changed files by comparing Drive metadata with local index state
- Keep synchronization separate from queries: begin with an explicit Sync command and show index freshness
- Target a local PySide6 desktop application after the command-line RAG MVP works
- Keep model providers replaceable; defer the LLM/provider choice until grounded retrieval is working
- Use synthetic data until authorization and external-service data policies are confirmed for real lab records
