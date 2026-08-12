import math
from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

FEATURES = [
    "burst_release",
    "particle_size",
    "stirring_speed",
    "control",
]

DOCUMENTS = [
    {
        "source": "release_study_may.txt",
        "experiment_id": "experiment_17",
        "text": """
The formulation used PLGA with 2% PVA and was stirred at 800 RPM.

The experiment showed high initial burst release during the first 24 hours.

Particle size remained within the expected range.
""".strip(),
    },
    {
        "source": "particle_study_june.txt",
        "experiment_id": "experiment_24",
        "text": """
The stirring speed was reduced from 800 RPM to 400 RPM.

The resulting particles were larger than expected.

No unusual burst release was observed.
""".strip(),
    }, 
    {
    "source": "control_study_may.txt",
    "experiment_id": "control_01",
    "text": """
The control batch used the standard formulation and standard processing conditions.

Particle size remained within the expected target range.

The release profile was gradual, with no pronounced initial burst release.
""".strip(),
}
]


CHUNK_VECTORS = {
    # Experiment 17
    "experiment_17_chunk_1": [0.0, 0.0, 1.0, 0.0],
    "experiment_17_chunk_2": [1.0, 0.0, 0.0, 0.0],
    "experiment_17_chunk_3": [0.0, 1.0, 0.0, 0.0],

    # Experiment 24
    "experiment_24_chunk_1": [0.0, 0.0, 1.0, 0.0],
    "experiment_24_chunk_2": [0.0, 1.0, 0.0, 0.0],
    "experiment_24_chunk_3": [1.0, 0.0, 0.0, 0.0],

    # Control experiment
    "control_01_chunk_1": [0.0, 0.0, 0.0, 1.0],
    "control_01_chunk_2": [0.0, 1.0, 0.0, 1.0],
    "control_01_chunk_3": [1.0, 0.0, 0.0, 1.0],
}

def add_manual_vectors(
    chunks: list[dict],
    vectors: dict[str, list[float]],
) -> list[dict]:
    """Add manually defined vectors to the chunks."""
    result = []
    for chunk in chunks:
        chunk_copy = chunk.copy()
        chunk_id = chunk_copy["chunk_id"]
        if chunk_id in vectors:
            chunk_copy["vector"] = vectors[chunk_id]
            result.append(chunk_copy)
        else:
            raise KeyError(f"No vector found for chunk_id: {chunk_id}")
    return result

def cosine_similarity(
    vector_a: list[float],
    vector_b: list[float],
) -> float:
    if len(vector_a) != len(vector_b):
        raise ValueError("Vectors must have equal dimensions")

    dot_product = math.sumprod(vector_a, vector_b)
    magnitude_a = math.sqrt(sum(x ** 2 for x in vector_a))
    magnitude_b = math.sqrt(sum(x ** 2 for x in vector_b))

    if magnitude_a == 0 or magnitude_b == 0:
        raise ValueError("Cosine similarity is undefined for zero vectors")

    return dot_product / (magnitude_a * magnitude_b)

def create_chunks(documents: list[dict]) -> list[dict]:
    """Convert synthetic documents into paragraph-level chunks."""
    chunks = []
    for doc in documents:
        paragraphs = doc["text"].split("\n\n")
        for i, paragraph in enumerate(paragraphs):
            chunk = {
                "source": doc["source"],
                "experiment_id": doc["experiment_id"],
                "chunk_id": f"{doc['experiment_id']}_chunk_{i+1}",
                "text": paragraph.strip(),
            }
            chunks.append(chunk)
    return chunks

def retrieve(
    query_vector: list[float],
    chunks: list[dict],
    top_k: int,
) -> list[dict]:
    """Return the top-k chunks ranked by cosine similarity."""
    if top_k <= 0:
           raise ValueError("top_k must be greater than zero")
    
    if not chunks:
        return []

    if len(query_vector) != len(chunks[0]["vector"]):
        raise ValueError("Query vector and chunk vectors must have equal dimensions")

    scored_chunks = []
    for chunk in chunks:
        score = cosine_similarity(query_vector, chunk["vector"])
        chunk_copy = chunk.copy()
        chunk_copy["score"] = score
        scored_chunks.append((score, chunk_copy))

    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    top_chunks = [chunk for score, chunk in scored_chunks[:top_k]]
    return top_chunks

def add_embeddings(
        chunks: list[dict],
        model: SentenceTransformer,
) -> list[dict]:
    """Embed chunk text and return copies containing vectors."""
    result = []
    texts = [chunk["text"] for chunk in chunks]
    embeddings = model.encode(texts)
    for chunk, embedding in zip(chunks, embeddings):
        chunk_copy = chunk.copy()
        chunk_copy["vector"] = embedding.tolist()
        result.append(chunk_copy)
    return result

if __name__ == "__main__":
    model = SentenceTransformer(MODEL_NAME)

    chunks = create_chunks(DOCUMENTS)
    embedded_chunks = add_embeddings(chunks, model)

    query = "Which experiment released material rapidly at the beginning?"
    query_vector = model.encode(query).tolist()

    results = retrieve(
        query_vector=query_vector,
        chunks=embedded_chunks,
        top_k=3,
    )

    for rank, result in enumerate(results, start=1):
        print(f"\n{rank}. Score: {result['score']:.3f}")
        print(f"Experiment: {result['experiment_id']}")
        print(f"Source: {result['source']}")
        print(f"Text: {result['text']}")