# -*- coding: utf-8 -*-
"""Chạy benchmark theo hướng dẫn data/README.md, dùng LocalEmbedder."""

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from data.benchmark_queries import BENCHMARK_QUERIES
from ingest import build_knowledge_base
from src import LocalEmbedder
from src.chunking import CustomChunker, RecursiveChunker


def run_one(chunker, name, embedder):
    store = build_knowledge_base(
        "data/k4_ecommerce",
        embedding_fn=embedder,
        chunker=chunker,
        collection_name=f"benchmark-{name}",
    )
    print(f"\n{'='*70}")
    print(f"  CHIẾN LƯỢC: {name}  |  Chunks: {store.get_collection_size()}")
    print(f"{'='*70}")

    hits = 0
    for item in BENCHMARK_QUERIES:
        results = store.search_with_filter(
            item["query"],
            top_k=3,
            metadata_filter=item["metadata_filter"],
        )
        print(f"\n{item['id']}: {item['query']}")
        found = False
        for rank, result in enumerate(results, 1):
            doc_id = result["metadata"].get("doc_id")
            mark = " ✓" if doc_id == item["relevant_doc_id"] else ""
            if mark:
                found = True
            print(f"{rank}. score={result['score']:.4f} doc={doc_id}{mark}")
            print(f"   {result['content'][:300].replace(chr(10), ' ')}")
        if found:
            hits += 1
            print("=> ✓ HIT")
        else:
            print("=> ✗ MISS")

    print(f"\n>> {name}: {hits}/5 hits")
    return hits


embedder = LocalEmbedder()
print("Embedder:", embedder._backend_name)

# Baseline: RecursiveChunker
run_one(RecursiveChunker(chunk_size=500), "RecursiveChunker-500", embedder)

# Custom: CustomChunker
run_one(CustomChunker(max_chunk_size=1000), "CustomChunker-1000", embedder)
