"""
One-time seed: loads data/jobs_corpus.json (static 483-record sourced up front) into Postgres + FAISS + BM25.
"""
import json
import sys
import os
from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.dialects.postgresql import insert
from app.models.base import Base, engine, SessionLocal
from app.models.job import Job
from app.services.embeddings import embed_batch
from app.services.vector_index import get_index
from app.services.bm25_index import get_bm25_index

CORPUS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "jobs_corpus.json")


def dedup_key(title: str, company: str, location: str | None) -> str:
    import re
    def clean(s):
        return re.sub(r"[^a-z0-9]+", " ", (s or "").lower().strip()).strip()
    return f"{clean(title)}|{clean(company)}|{clean(location or '')}"


def main():
    Base.metadata.create_all(engine)
    db = SessionLocal()

    with open(CORPUS_PATH) as f:
        records = json.load(f)
    print(f"Loaded {len(records)} records from {CORPUS_PATH}")

    existing_keys = {row.dedup_key for row in db.query(Job.dedup_key).all()}

    new_records = []
    for r in records:
        row_id = f"{r['source']}:{r['id']}"
        key = dedup_key(r["title"], r["company"], r.get("location"))
        if key in existing_keys:
            continue
        new_records.append((row_id, key, r))

    print(f"{len(new_records)} new after dedup against existing DB rows")

    if not new_records:
        print("Nothing new to seed.")
        return

    descriptions = [r["description"] for _, _, r in new_records]
    print("Embedding descriptions (this loads the model, ~1-2s)...")
    embeddings = embed_batch(descriptions)

    row_ids = []
    for row_id, key, r in new_records:
        stmt = insert(Job).values(
            id=row_id,
            source=r["source"],
            source_job_id=r["id"],
            dedup_key=key,
            title=r["title"],
            company=r["company"],
            location=r.get("location"),
            description=r["description"],
            url=r.get("url"),
            salary_min=r.get("salary_min"),
            salary_max=r.get("salary_max"),
            employment_type=r.get("employment_type"),
            posted_at=r.get("posted_at"),
        ).on_conflict_do_nothing(index_elements=["id"])
        db.execute(stmt)
        row_ids.append(row_id)
    db.commit()
    print(f"Inserted {len(row_ids)} rows into Postgres")

    get_index().add(row_ids, embeddings)
    print(f"FAISS index now has {get_index().size} vectors")

    all_jobs = db.query(Job.id, Job.description).all()
    get_bm25_index().rebuild([j.id for j in all_jobs], [j.description for j in all_jobs])
    print(f"BM25 index rebuilt over {get_bm25_index().size} documents")

    db.close()
    print("Seed complete.")


if __name__ == "__main__":
    main()
