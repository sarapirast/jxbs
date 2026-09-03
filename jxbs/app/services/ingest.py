import re
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from ..sources.registry import get_active_sources
from ..sources.base import NormalizedJob
from ..models.job import Job
from .embeddings import embed_batch
from .vector_index import get_index
from .bm25_index import get_bm25_index


def _normalize_key(title: str, company: str, location: str | None) -> str:
    """Collapse whitespace/case/punctuation so near-identical postings from
    different sources map to the same key."""
    def clean(s: str) -> str:
        s = (s or "").lower().strip()
        return re.sub(r"[^a-z0-9]+", " ", s).strip()
    return f"{clean(title)}|{clean(company)}|{clean(location or '')}"


def run_ingest(db: Session, queries: list[str], locations: list[str], max_results_per_query: int = 25) -> dict:
    """
    Pulls postings for every (query, location) pair from every configured
    source, deduplicates, embeds new descriptions, and upserts.

    Returns a summary dict
    """
    sources = get_active_sources()
    if not sources:
        return {"error": "No job sources configured — check your .env for API keys."}

    fetched: list[NormalizedJob] = []
    per_source_counts = {}
    for source in sources:
        for query in queries:
            for location in locations:
                try:
                    results = source.fetch(query, location, max_results=max_results_per_query)
                    fetched.extend(results)
                    per_source_counts[source.name] = per_source_counts.get(source.name, 0) + len(results)
                except Exception as e:
                    print(f"[ingest] {source.name} failed for '{query}' in '{location}': {e}")

    # Dedup within this batch by dedup_key, keeping the first occurrence
    seen_keys: dict[str, NormalizedJob] = {}
    for job in fetched:
        key = _normalize_key(job.title, job.company, job.location)
        if key not in seen_keys:
            seen_keys[key] = job

    existing_keys = {row.dedup_key for row in db.query(Job.dedup_key).all()}
    new_jobs = [(k, j) for k, j in seen_keys.items() if k not in existing_keys]

    if not new_jobs:
        return {
            "fetched": len(fetched),
            "unique_in_batch": len(seen_keys),
            "new": 0,
            "per_source": per_source_counts,
        }

    embeddings = embed_batch([j.description for _, j in new_jobs])

    inserted = 0
    row_ids = []
    for (key, job), embedding in zip(new_jobs, embeddings):
        row_id = f"{job.source}:{job.source_job_id}"
        stmt = insert(Job).values(
            id=row_id,
            source=job.source,
            source_job_id=job.source_job_id,
            dedup_key=key,
            title=job.title,
            company=job.company,
            location=job.location,
            description=job.description,
            url=job.url,
            salary_min=job.salary_min,
            salary_max=job.salary_max,
            employment_type=job.employment_type,
            posted_at=job.posted_at,
        ).on_conflict_do_nothing(index_elements=["id"])
        db.execute(stmt)
        row_ids.append(row_id)
        inserted += 1
    db.commit()

    get_index().add(row_ids, embeddings)

    all_jobs = db.query(Job.id, Job.description).all()
    get_bm25_index().rebuild(
        job_ids=[j.id for j in all_jobs],
        texts=[j.description for j in all_jobs],
    )

    return {
        "fetched": len(fetched),
        "unique_in_batch": len(seen_keys),
        "new": inserted,
        "per_source": per_source_counts,
    }
