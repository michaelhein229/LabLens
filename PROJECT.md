# LabLens — Agentic RAG Research Assistant

## Project Goal

Build **LabLens**, a research knowledge assistant that connects to a Google Drive folder containing laboratory notes, Google Slides, documents, PDFs, and experiment records.

The system will ingest and structure this information, index it for retrieval, and allow a researcher to ask natural-language questions about previous experiments.

The final system should be able to:

* Search past experimental notes semantically.
* Search using exact keywords and metadata.
* Retrieve evidence from specific presentations, slides, documents, and experiments.
* Compare related experiments.
* Answer questions using retrieved evidence.
* Cite the original source for every important claim.
* Use agents/tools to select appropriate retrieval strategies.
* Generate summaries or research documents from retrieved information.
* Detect new or modified files in Google Drive and update the knowledge base.
* Avoid making unsupported scientific claims.

The purpose of this project is also educational. I want to **learn how RAG and agentic retrieval systems actually work**, rather than having frameworks abstract everything away.

---

# Current Implementation Snapshot

Updated 2026-08-13.

LabLens is transitioning from Milestone 2, Drive Connected, into Milestone 3, Lab Data Extracted.

Current working code can:

* Run the RAG fundamentals warmup with synthetic documents, paragraph chunks, Sentence Transformer embeddings, cosine similarity, and deterministic retrieval tests.
* Authenticate with Google Drive using local OAuth credentials and a local token outside Git.
* Read a configured Drive folder ID from local environment configuration.
* List paginated direct children of that Drive folder.
* Normalize raw Drive API file dictionaries into a shared Pydantic `DriveFileMetadata` model.
* Route normalized Drive files by MIME type for Google Slides, Google Docs, PDFs, folders, and unsupported files.

Current test status:

```text
26 passing tests
```

Important current files:

```text
src/lablens/models/models.py              Shared Pydantic models
src/lablens/ingestion/google_drive.py     Drive folder listing and metadata normalization
src/lablens/ingestion/google_auth.py      Google OAuth/service setup
src/lablens/extraction/router.py          MIME-type routing
src/lablens/extraction/google_slides.py   Next extractor target
tests/ingestion/test_google_drive.py      Drive normalization and pagination tests
tests/extraction/test_router.py           MIME router tests
```

Current next task:

```text
Extract slide-level text records from Google Slides API presentation data.
```

Do not start embeddings, vector storage, agents, or desktop UI until at least one Google Slides presentation can be extracted into structured slide-level records with source metadata.

---

# Important Teaching Instructions

Do not build the entire project for me.

Treat this project like a guided software engineering course where I implement the system incrementally.

At the beginning of each work session, give me a small set of **Today's Assignments**.

Each assignment should:

1. Explain what we are building.
2. Explain why the component exists.
3. Explain how it fits into the overall architecture.
4. Provide the concepts I need to understand before implementing it.
5. Provide relevant official documentation or high-quality learning resources.
6. Give me a concrete implementation task.
7. Define what successful completion looks like.
8. Give me a way to test the implementation.
9. Avoid giving me the complete implementation unless I explicitly ask for it.

Prefer teaching through hints, pseudocode, APIs, function signatures, diagrams, examples, and debugging guidance.

If I get stuck, progressively provide more help.

Do not immediately replace my implementation with your own.

When reviewing code I write:

* Explain what is correct.
* Identify bugs or architectural problems.
* Explain why they occur.
* Let me attempt the fix when practical.
* Provide the full corrected implementation only when necessary or explicitly requested.

The goal is for me to be able to explain the architecture and implementation in a technical interview.

---

# Development Philosophy

Start simple.

Do not introduce agents, LangChain, LlamaIndex, complex orchestration frameworks, or unnecessary infrastructure until the underlying RAG pipeline works.

Initially implement major RAG components ourselves using normal Python and APIs.

Libraries may be used for:

* Google APIs
* parsing documents
* embedding models
* vector databases
* model APIs
* tokenization
* standard infrastructure

But avoid libraries that hide the entire RAG pipeline early in the project.

I should understand:

* document ingestion
* chunking
* embeddings
* vector similarity
* indexing
* retrieval
* metadata
* query construction
* prompt construction
* context windows
* reranking
* hybrid retrieval
* retrieval evaluation
* grounded generation
* tool calling
* agent orchestration

before relying heavily on higher-level abstractions.

---

# Target Architecture

The mature system should approximately follow:

```text
                    GOOGLE DRIVE
                         |
                         v
                Drive Synchronization
                         |
                         v
              Document Type Detection
                         |
          +--------------+--------------+
          |              |              |
          v              v              v
       Slides          Docs            PDFs
          |              |              |
          +--------------+--------------+
                         |
                         v
                 Content Extraction
                         |
                         v
              Cleaning / Normalization
                         |
                         v
                Semantic Chunking
                         |
                         v
              Metadata Enrichment
                         |
             +-----------+-----------+
             |                       |
             v                       v
       Embedding Index          Keyword Index
        / Vector DB
             |                       |
             +-----------+-----------+
                         |
                         v
                  Retrieval Layer
                         |
       +-----------------+------------------+
       |                 |                  |
       v                 v                  v
 Semantic Search   Keyword Search    Metadata Filtering
       |                 |                  |
       +-----------------+------------------+
                         |
                         v
                   Result Reranking
                         |
                         v
                 Retrieved Evidence
                         |
                         v
                Agent / LLM Reasoning
                         |
             +-----------+------------+
             |                        |
             v                        v
       Grounded Answer          Artifact Generation
             |                        |
             v                        v
       Source Citations          Google Docs / Reports
```

---

# Phase 0 — RAG Fundamentals

Before beginning the main application, make sure I understand a basic RAG pipeline.

Teach and demonstrate:

```text
Document
    ↓
Chunks
    ↓
Embeddings
    ↓
Vector Index
    ↓
Query Embedding
    ↓
Similarity Search
    ↓
Retrieved Context
    ↓
LLM Prompt
    ↓
Grounded Answer
```

I should understand what each part is doing rather than only how to call a library.

Topics:

* embeddings
* cosine similarity
* semantic similarity
* vector databases
* chunk size
* chunk overlap
* top-k retrieval
* context windows
* retrieval vs generation

Have me build a very small RAG example before connecting Google Drive.

---

# Phase 1 — Project Foundation

Create a clean Python project structure.

Possible structure:

```text
lablens/
│
├── src/
│   ├── ingestion/
│   ├── extraction/
│   ├── indexing/
│   ├── retrieval/
│   ├── agents/
│   ├── generation/
│   └── evaluation/
│
├── tests/
├── scripts/
├── data/
├── .env.example
├── requirements.txt
└── README.md
```

Teach:

* separation of concerns
* environment variables
* configuration
* API credentials
* dependency management
* secrets management

Do not overengineer the project structure at the beginning.

The first working interface should be command-line based. Keep core behavior in
reusable Python modules so a desktop UI can call the same ingestion, indexing,
retrieval, and generation services later.

---

# Phase 2 — Google Drive Integration

Connect the application to a specific Google Drive folder.

The system should eventually:

* authenticate using Google OAuth
* access only the required Drive files
* list files inside the selected folder
* recursively inspect folders if needed
* retrieve file metadata
* identify supported file types

Important metadata:

```text
file_id
file_name
mime_type
created_time
modified_time
folder
web_url
```

The Drive folder ID must be runtime configuration rather than hardcoded. Each
user should be able to authorize with their own Google account and point the
same application at a different accessible folder.

Drive discovery should initially list direct children. Add pagination next,
then recursive traversal as a deliberate extension. Convert Google API field
names into a stable internal record before extraction code consumes them.

Teach me:

* OAuth
* access tokens
* refresh tokens
* Drive API scopes
* Google Drive file IDs
* MIME types
* Google API pagination

Initial milestone:

```text
Google Drive Folder
        ↓
Python script
        ↓
List all files + metadata
```

Do not involve embeddings yet.

---

# Phase 3 — Google Slides and Document Extraction

Support content extraction from:

1. Google Slides
2. Google Docs
3. PDFs

Prioritize Google Slides because experiment information may be organized slide-by-slide.

For Slides, preserve:

```text
presentation
slide number
slide ID
slide title
text
speaker notes if accessible
source URL
```

We should preserve slide boundaries.

Do not immediately concatenate an entire presentation into one string.

Example extracted structure:

```json
{
  "file_id": "...",
  "presentation": "PLGA Experiments July",
  "slide_number": 14,
  "slide_id": "...",
  "text": "Experiment 24 ...",
  "modified_time": "...",
  "source_url": "..."
}
```

Teach how the Slides API represents:

* presentations
* slides
* page elements
* shapes
* text runs

Later investigate tables, charts, images, and speaker notes.

---

# Phase 4 — Content Cleaning and Normalization

Create a preprocessing layer.

Responsibilities may include:

* removing useless whitespace
* preserving units
* preserving experiment IDs
* preserving scientific abbreviations
* preserving dates
* handling bullet points
* combining logically connected slide elements
* maintaining source references

Never silently rewrite scientific observations.

The raw extracted text should remain available alongside cleaned text.

Suggested structure:

```python
DocumentChunk(
    raw_text=...,
    clean_text=...,
    metadata=...
)
```

---

# Phase 5 — Chunking

Build chunking ourselves before using framework abstractions.

Start with simple strategies and compare them.

Explore:

### Fixed token chunking

```text
500 tokens
50-token overlap
```

### Slide-based chunking

One slide = one chunk.

### Semantic / experiment-aware chunking

Keep together:

```text
Experiment
Conditions
Procedure
Observation
Result
Interpretation
```

The project should eventually determine whether experiment-aware chunks outperform naive fixed-length chunks.

Teach:

* why chunks are necessary
* chunk size tradeoffs
* chunk overlap
* semantic boundaries
* retrieval granularity
* context loss

---

# Phase 6 — Embeddings

Generate embeddings for each chunk.

Start with an embedding API or a local embedding model.

The implementation should make the embedding provider replaceable.

Example interface:

```python
class EmbeddingProvider:
    def embed_documents(self, texts):
        ...

    def embed_query(self, query):
        ...
```

Teach:

* embedding dimensions
* semantic similarity
* document embeddings vs query embeddings
* batching
* token limits
* embedding cost
* normalization

Do not treat embeddings as magic.

---

# Phase 7 — Vector Database

Start with a simple local vector store such as:

* Chroma
* FAISS

The initial index should persist to local disk. Document embeddings are created
during indexing and must survive application restarts; they should not be
recomputed for every question. At query time, normally embed only the new query
and search the stored document vectors.

Store:

```text
embedding
chunk text
document ID
presentation
slide number
experiment ID
date
source URL
other metadata
```

Build the retrieval call ourselves.

Example conceptual interface:

```python
results = vector_store.search(
    query_embedding,
    top_k=5
)
```

Each result should include:

```text
similarity score
chunk
metadata
source
```

Teach what approximate nearest-neighbor search is at a conceptual level.

Store the embedding model identifier with index metadata. Embeddings produced
by different models should not be mixed silently in one index. Changing the
embedding model, extractor behavior, or chunking strategy may require an index
version change and re-indexing.

---

# Phase 8 — First Semantic Search MVP

Before using an LLM, create a search interface.

Example:

```text
Query:
"experiments with high burst release"

Results:

1. Experiment 24
   PLGA Experiments July
   Slide 14
   Similarity: ...

2. Experiment 17
   Release Study
   Slide 22
   Similarity: ...
```

This milestone should prove that retrieval itself works.

Do not hide poor retrieval behind an LLM.

---

# Phase 9 — Basic RAG

Add an LLM such as Gemini or another model.

Pipeline:

```text
User Question
      ↓
Embed Question
      ↓
Retrieve top-k chunks
      ↓
Construct context
      ↓
Construct prompt
      ↓
LLM
      ↓
Answer
```

The model must distinguish between:

* information found in retrieved evidence
* inference
* information not available

Every important experimental claim should be traceable to its source.

Example response:

```text
You documented high burst release in Experiments 17 and 24.

Experiment 24 used ...
Experiment 17 used ...

Sources:
- PLGA Experiments July — Slide 14
- Release Study May — Slide 22
```

This is the **first complete LabLens MVP**.

---

# Phase 10 — Retrieval Evaluation

Before adding agents, create an evaluation dataset.

Example:

```json
{
  "question": "Which experiments showed high burst release?",
  "expected_sources": [
    "experiment_17",
    "experiment_24"
  ]
}
```

Measure concepts such as:

* Recall@K
* Precision@K
* Mean Reciprocal Rank where appropriate
* source retrieval accuracy
* citation accuracy

Teach me how to evaluate retrieval independently from generation.

Create approximately 20–50 representative questions over time.

---

# Phase 11 — Metadata Retrieval

Add structured metadata filters.

Possible fields:

```text
experiment_id
experiment_date
polymer
material
method
concentration
particle_size
research_project
presentation
researcher
```

Support questions like:

```text
"PLGA experiments from the last six months"

"Experiments using 2% PVA"

"Experiments from May involving burst release"
```

Combine semantic retrieval with metadata filtering.

---

# Phase 12 — Keyword / Lexical Retrieval

Add keyword search, potentially using BM25.

Explain where keyword search is stronger than embeddings.

Examples:

```text
"PLGA 50:50"
"Batch 27"
"800 RPM"
"2% PVA"
```

These may benefit from exact lexical retrieval.

---

# Phase 13 — Hybrid Retrieval

Combine:

```text
semantic vector search
+
keyword/BM25 search
+
metadata filters
```

Experiment with score combination and ranking.

Evaluate hybrid retrieval against semantic-only retrieval.

Do not assume hybrid retrieval is automatically better.

Measure it.

---

# Phase 14 — Query Rewriting and Expansion

Some user questions will not be good retrieval queries.

Example:

```text
"Did what happened today ever happen before?"
```

A query-understanding step might produce:

```text
"PLGA experiments with unusually large particles"

"experiments with increased initial burst release"

"experiments involving 2% PVA and abnormal particle size"
```

Teach:

* query rewriting
* query expansion
* multi-query retrieval
* decomposition

Allow an LLM such as Gemini to generate retrieval queries.

Compare retrieval quality before and after rewriting.

---

# Phase 15 — Reranking

Add a reranking layer.

Pipeline:

```text
retrieve 20 candidates
        ↓
reranker
        ↓
best 5 pieces of evidence
```

Explore:

* LLM reranking
* cross-encoder reranking
* heuristic reranking

Measure whether reranking improves retrieval quality.

---

# Phase 16 — Experiment-Aware Structured Extraction

Introduce optional LLM-assisted structured extraction.

Transform messy notes such as:

```text
Batch 7
5%
particles way larger
maybe stirring speed?
compare May 14
```

into structured information such as:

```json
{
  "experiment": "Batch 7",
  "conditions": {
    "concentration": "5%"
  },
  "observations": [
    "Particle size larger than expected"
  ],
  "hypotheses": [
    "Stirring speed may contribute"
  ],
  "related_experiments": [
    "May 14"
  ]
}
```

Important:

The structured representation must never replace the original source.

Always retain:

```text
raw source
structured representation
source location
```

Structured extraction should be considered derived data.

---

# Phase 17 — Retrieval Tools

Turn retrieval capabilities into explicit tools.

Examples:

```python
semantic_search(query)

keyword_search(query)

search_experiments(filters)

get_experiment(experiment_id)

get_slide(file_id, slide_number)

find_related_experiments(experiment_id)
```

Each tool should have:

* a clear responsibility
* validated inputs
* structured outputs
* tests

---

# Phase 18 — Coordinator Agent

Introduce the first real agent.

The coordinator determines which tools should answer a question.

Example:

```text
User:
"Compare my PLGA experiments from the last six months
where burst release was high."

Coordinator:

1. Filter experiments:
   material = PLGA
   date >= six months ago

2. Semantic search:
   high initial release / burst release

3. Keyword search:
   "burst release"

4. Merge results.

5. Rerank.

6. Send evidence to synthesis.
```

The coordinator should not hallucinate retrieval results.

It must operate through tools.

---

# Phase 19 — Evidence / Synthesis Agent

Create an agent responsible for synthesizing retrieved evidence.

Responsibilities:

* compare experiments
* identify similarities
* identify differences
* summarize observations
* identify missing information
* produce citations

It should clearly separate:

```text
Documented observation
vs.
Model inference
```

Avoid presenting model speculation as experimental fact.

---

# Phase 20 — Experiment Comparison

Build structured comparison workflows.

Example user query:

```text
Compare experiments 14, 17, and 24.
```

Possible output:

| Variable      | Exp 14 | Exp 17 | Exp 24 |
| ------------- | ------ | ------ | ------ |
| Polymer       | ...    | ...    | ...    |
| PVA           | ...    | ...    | ...    |
| RPM           | ...    | ...    | ...    |
| Particle size | ...    | ...    | ...    |
| Burst release | ...    | ...    | ...    |

Then generate a textual summary grounded in those records.

---

# Phase 21 — Artifact Generation

Allow users to request generated research artifacts.

Examples:

```text
"Make a summary of every particle-size experiment this year."

"Generate a comparison report for the experiments that showed high burst release."

"Create a one-page overview of what we know about PVA concentration."
```

Pipeline:

```text
Request
   ↓
Retrieval Plan
   ↓
Evidence Collection
   ↓
Synthesis
   ↓
Document Generation
   ↓
Google Doc
```

Generated documents must preserve citations to original evidence.

---

# Phase 22 — Google Docs Integration

Allow the system to create documents in Google Drive.

Generated documents should contain:

```text
Title
Date generated
User query
Summary
Evidence
Experiment comparisons
Source references
```

Generated content should be clearly distinguishable from original lab records.

---

# Phase 23 — Drive Synchronization

The system should not re-index the entire Drive folder every time it runs.

Track:

```text
file_id
modified_time
content_hash
indexed_at
extractor_version
chunking_version
embedding_model
status
```

Workflow:

```text
Check Drive
    ↓
New file?
    → ingest

Modified file?
    → reprocess

Unchanged?
    → skip
```

Eventually investigate handling deleted files as well.

Synchronization should be separate from the normal query path. Begin with an
explicit update operation such as:

```text
Sync Drive
    ↓
compare current Drive metadata with local index state
    ↓
extract, chunk, embed, and replace only new or changed files
    ↓
record last successful synchronization time
```

Queries should use the last complete local index and should not normally wait
for a full Drive scan. The first user experience should expose a manual sync
command and last-synchronized timestamp. Later options may include startup
checks, periodic background synchronization, or the Drive Changes API.

For an updated file, build and validate its replacement chunks before removing
the prior indexed version when practical. Treat missing files carefully because
they may have been deleted, moved outside the configured folder, or made
inaccessible.

---

# Phase 24 — Production Concerns

Once the system works locally, discuss:

* authentication
* permissions
* API quotas
* retry logic
* caching
* logging
* rate limiting
* model costs
* vector database persistence
* concurrency
* background indexing
* deployment
* secrets management

Do not introduce production complexity before the core system works.

---

# Desktop Application Direction

After the command-line RAG MVP works, package LabLens as a local desktop
application. PySide6 is the initial preferred UI toolkit because it can call the
Python core directly and supports macOS, Windows, and Linux.

The UI should remain an orchestration and presentation layer:

```text
Desktop UI
    ↓
Application services
    ├── authorize Google Drive
    ├── select/configure a Drive folder
    ├── sync the local knowledge base
    ├── search or ask a question
    └── open a source citation
    ↓
Core LabLens modules
    ├── ingestion and extraction
    ├── chunking and embeddings
    ├── persistent vector storage
    ├── retrieval
    └── grounded generation
```

The first desktop experience should eventually show:

* configured Drive folder
* authorization status
* indexed file and chunk counts
* last successful synchronization time
* a visible Sync Drive action with progress and errors
* question/search input
* grounded answers or search results
* clickable citations to the original Slides, Docs, or PDF locations

Synchronization should run outside the UI thread. During a sync, queries may
continue using the last complete index. Do not begin GUI implementation until a
command-line vertical slice can ingest, persist, retrieve, and cite at least one
Google Slides presentation.

---

# Phase 25 — Privacy and Research Data Safety

This project may contain unpublished scientific research.

Treat all lab data as sensitive.

Do not assume it is acceptable to send full documents to external AI services.

Architecture should minimize unnecessary exposure.

Consider:

* least-privilege Google OAuth scopes
* local document processing
* local vector storage
* only sending necessary retrieved chunks to the LLM
* encrypted secrets
* access controls
* avoiding logging sensitive document contents

Before using real lab data, confirm that the researcher is allowed to process the data using the selected external APIs.

During early development, use synthetic/sample experiment data when appropriate.

---

# Agent Design Philosophy

Do not create an agent for every function.

Prefer deterministic code when possible.

Good use of normal code:

```text
file parsing
chunking
embedding
database operations
metadata filtering
sorting
authentication
synchronization
```

Potentially good uses for LLMs/agents:

```text
query interpretation
query rewriting
query decomposition
structured extraction
retrieval planning
evidence synthesis
document generation
```

Use agents only when reasoning or dynamic tool selection provides meaningful value.

---

# Model Provider Design

Do not tightly couple the entire application to Gemini, OpenAI, Claude, or another provider.

Prefer interfaces such as:

```python
class LLMProvider:
    def generate(...):
        ...

class EmbeddingProvider:
    def embed(...):
        ...
```

This should make it possible to experiment with:

```text
Gemini
OpenAI
Claude
local models
```

without rebuilding the entire architecture.

---

# Testing Strategy

Tests should be introduced throughout the project rather than at the end.

Test:

* Drive metadata parsing
* Slides extraction
* document cleaning
* chunking
* metadata preservation
* vector insertion
* retrieval
* metadata filtering
* keyword retrieval
* query rewriting
* tool outputs
* citations
* synchronization

Prefer small deterministic unit tests where possible.

Use integration tests for APIs.

---

# Git Workflow

Encourage small commits corresponding to project milestones.

Examples:

```text
feat: authenticate with Google Drive

feat: extract text from Google Slides

feat: add slide metadata model

feat: implement token-based chunker

feat: create embedding provider

feat: add Chroma vector index

feat: implement semantic retrieval

feat: add grounded Gemini responses

feat: implement retrieval evaluation

feat: add hybrid search

feat: add query rewriting

feat: add coordinator agent
```

Do not generate dozens of unrelated files in one step.

---

# Daily Assignment Format

At the start of each development session, respond using this structure:

## Today's Goal

Explain the single larger outcome we are working toward.

## Concepts to Learn

Explain the minimum concepts required for today's work.

## Resources

Provide relevant documentation and resources.

Prioritize:

1. official documentation
2. authoritative technical guides
3. high-quality tutorials only when useful

Explain what section of each resource I should focus on.

## Assignment 1

### Objective

What I will build.

### Why It Matters

How it contributes to LabLens.

### Requirements

Concrete implementation requirements.

### Hints

Architecture guidance, pseudocode, or relevant APIs.

Do not give the full implementation unless requested.

### Success Criteria

Example:

```text
Running:

python scripts/list_drive_files.py

should produce:

PLGA Experiments July | Google Slides | modified 2026-07-14
Release Study May     | Google Slides | modified 2026-05-22
Lab Notes             | Google Docs   | modified 2026-08-02
```

### Testing

Explain how I can prove the assignment works.

---

Repeat the structure for Assignment 2, Assignment 3, etc.

Keep normal sessions to approximately **2–4 meaningful assignments**.

Assignments should build on one another.

Do not give me twenty tasks at once.

---

# End-of-Session Review

When I finish the day's assignments:

1. Review what was implemented.
2. Identify anything that should be fixed before moving on.
3. Ask me conceptual questions to verify understanding.
4. Summarize what the system can now do.
5. Identify the next architectural milestone.

Example conceptual questions:

```text
Why do we embed chunks instead of entire presentations?

Why might keyword search outperform vector search for "PLGA 50:50"?

What information would be lost if we did not preserve slide metadata?

Why should retrieved documents be evaluated separately from the LLM answer?
```

The goal is for me to understand the system deeply enough to explain these decisions without assistance.

---

# Project Milestones

Use these major milestones to track progress.

## Milestone 1 — RAG Fundamentals

I can explain and implement a simple RAG pipeline.

## Milestone 2 — Drive Connected

The system can authenticate and discover lab files.

## Milestone 3 — Lab Data Extracted

Slides, Docs, and PDFs can be converted into structured records.

## Milestone 4 — Semantic Search

Lab notes can be searched using embeddings.

## Milestone 5 — RAG MVP

Users can ask questions and receive grounded answers with source citations.

## Milestone 6 — Evaluated Retrieval

We can measure whether retrieval is actually finding the correct evidence.

## Milestone 7 — Advanced Retrieval

Metadata, keyword search, hybrid retrieval, rewriting, and reranking improve search quality.

## Milestone 8 — Experiment Intelligence

The system understands experiments as structured entities rather than generic text chunks.

## Milestone 9 — Agentic Lab Assistant

An agent dynamically selects retrieval tools and synthesizes evidence.

## Milestone 10 — Research Artifacts

The system can create grounded experiment summaries and Google Docs.

## Milestone 11 — Continuous Knowledge Base

New and modified Drive content automatically becomes searchable.

## Milestone 12 — Portfolio-Ready System

The system has tests, evaluation results, documentation, architectural diagrams, and a polished demonstration.

---

# MVP Boundary

Do not let the scope of the full roadmap delay the MVP.

The initial MVP is complete when:

```text
Google Drive
    ↓
Google Slides extraction
    ↓
chunking
    ↓
embeddings
    ↓
vector database
    ↓
semantic retrieval
    ↓
Gemini/LLM
    ↓
answer with slide-level citations
```

The command-line MVP comes first. A desktop UI is a delivery milestone after
this pipeline is reliable, not a prerequisite for proving retrieval quality.

Everything after this should be treated as an improvement that solves an identified limitation.

---

# Portfolio Goal

Throughout development, help me document important engineering decisions and measurable improvements.

Keep notes on questions such as:

```text
Why did we choose our chunking strategy?

Why did semantic retrieval fail for certain queries?

How much did hybrid retrieval improve Recall@K?

When did query rewriting help?

When was an agent better than deterministic routing?

How do we prevent unsupported scientific claims?

How does incremental Drive indexing work?
```

These decisions will eventually become material for the README, resume, and technical interviews.

The final project should demonstrate that I understand not only how to use an LLM API, but how to build and evaluate a complete retrieval-augmented, agentic AI system.
