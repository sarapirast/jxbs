import sys
import os
import json
 
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
 
from app.services.embeddings import embed_batch
from app.services.vector_index import FaissJobIndex
from app.services.bm25_index import BM25JobIndex
 
CORPUS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "jobs_corpus.json")
OUTPUT_DIR = "local_output"
 
 
def main():
    with open(CORPUS_PATH) as f:
        records = json.load(f)
    print(f"Loaded {len(records)} records from {CORPUS_PATH}")
 
    row_ids = [f"{r['source']}:{r['id']}" for r in records]
    descriptions = [r["description"] for r in records]
 
    print("Embedding")
    embeddings = embed_batch(descriptions)
    print(f"Embedded {len(embeddings)} descriptions.")
 
    print("Building FAISS index...")
    index = FaissJobIndex(index_dir=OUTPUT_DIR)
    index.add(row_ids, embeddings)
    print(f"FAISS index built: {index.size} vectors.")
 
    print("Building BM25 index...")
    bm25 = BM25JobIndex(index_dir=OUTPUT_DIR)
    bm25.rebuild(job_ids=row_ids, texts=descriptions)
    print(f"BM25 index built: {bm25.size} documents.")
 
    print()
    print("  - faiss.index")
    print("  - faiss_ids.json")
    print("  - bm25.pkl")
 
 
if __name__ == "__main__":
    main()