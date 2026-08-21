import argparse

from sentence_transformers import SentenceTransformer

from lablens.storage.chroma import ChromaVectorStore
from lablens.indexing.embeddings import SentenceTransformerEmbeddingProvider


def main():
    # 1. Read query from command-line args
    parser = argparse.ArgumentParser(
        description="Search indexed Google Slides with a semantic query."
    )
    parser.add_argument(
        "--persist-path",
        default="data/chroma",
    )
    parser.add_argument(
        "--collection-name",
        default="lablens-slides",
    )
    parser.add_argument("query", nargs="?")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()
    query = args.query if args.query is not None else input("Query: ")
    query = query.strip()
    top_k = args.top_k

    if not query:
        raise ValueError("Query must not be blank")

    if top_k <= 0:
        raise ValueError("top_k must be greater than zero")

    # 9. Create SentenceTransformer model/provider
    model = SentenceTransformer("all-MiniLM-L6-v2")
    provider = SentenceTransformerEmbeddingProvider(model)

    # 11. Search vector store with the query
    query_vector = provider.embed_query(query)
    vector_store = ChromaVectorStore(
        persist_path=args.persist_path,
        collection_name=args.collection_name,
    )
    results = vector_store.search(
        query_vector=query_vector,
        top_k=top_k,
    )

    if not results:
        print("No results found.")
        return

    for index, result in enumerate(results, start=1):
        chunk = result.chunk
        print(f"\n{index}. {chunk.source_title} - Slide {chunk.source_position}")
        print(f"Score: {result.score:.4f}")
        print(f"Text: {chunk.text[:500]}")
        print(f"Source: {chunk.citation_url}")


if __name__ == "__main__":
    main()
