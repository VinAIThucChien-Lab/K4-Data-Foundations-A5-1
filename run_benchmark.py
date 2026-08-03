import sys
from ingest import build_knowledge_base
from src.embeddings import _mock_embed
from data.benchmark_queries import BENCHMARK_QUERIES

def main():
    print("Building Knowledge Base...")
    store = build_knowledge_base("data/k4_ecommerce", embedding_fn=_mock_embed)
    print(f"KB loaded {store.get_collection_size()} chunks.\n")

    print("Running Benchmark Queries...\n")
    for q_data in BENCHMARK_QUERIES:
        q_id = q_data["id"]
        query = q_data["query"]
        filt = q_data.get("metadata_filter")
        print(f"[{q_id}] Query: {query}")
        print(f"  Filter: {filt}")
        if filt:
            results = store.search_with_filter(query, top_k=3, metadata_filter=filt)
        else:
            results = store.search(query, top_k=3)
        
        found_relevant = False
        for idx, r in enumerate(results, 1):
            doc_id = r["metadata"].get("doc_id")
            score = r["score"]
            if doc_id == q_data.get("relevant_doc_id"):
                found_relevant = True
            print(f"  Top {idx}: Score={score:.4f}, doc_id={doc_id}, chunk_index={r['metadata'].get('chunk_index')}")
        print(f"  => Found relevant doc ({q_data.get('relevant_doc_id')}) in Top-3? {found_relevant}\n")

if __name__ == '__main__':
    main()
