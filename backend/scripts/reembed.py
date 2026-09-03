"""
Re-embeds every job already in Postgres with the CURRENT embedding model
(app/services/embeddings.py) and rebuilds the FAISS index from scratch.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app.models.base import SessionLocal
from app.models.job import Job
from app.services.embeddings import embed_batch
from app.services.vector_index import FaissJobIndex


def main():
    db = SessionLocal()
    jobs = db.query(Job.id, Job.description).all()
    print(f"Re-embedding {len(jobs)} jobs with the current model...")

    if not jobs:
        print("No jobs in Postgres — run seed_corpus.py first.")
        return

    descriptions = [j.description for j in jobs]
    row_ids = [j.id for j in jobs]

    embeddings = embed_batch(descriptions)
    print("Embedding complete.")

    index_dir = "data"
    for fname in ("faiss.index", "faiss_ids.json"):
        path = os.path.join(index_dir, fname)
        if os.path.exists(path):
            os.remove(path)
            print(f"Removed old {path}")

    index = FaissJobIndex(index_dir=index_dir)
    index.add(row_ids, embeddings)
    print(f"New FAISS index built: {index.size} vectors, dim={len(embeddings[0])}")

    db.close()
    print("Re-embed complete. BM25 index untouched (no changes needed there).")


if __name__ == "__main__":
    main()
