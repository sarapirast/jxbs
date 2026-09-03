from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Literal

from ..models.base import get_db
from ..models.job import Job
from ..services.hybrid_search import bm25_search, vector_search, hybrid_search

router = APIRouter()


def _hydrate(db: Session, ranked: list[tuple[str, float]]) -> list[dict]:
    """Turns [(job_id, score), ...] into full job records, preserving rank order."""
    if not ranked:
        return []
    ids = [jid for jid, _ in ranked]
    rows = {j.id: j for j in db.query(Job).filter(Job.id.in_(ids)).all()}
    out = []
    for jid, score in ranked:
        job = rows.get(jid)
        if job is None:
            continue  # index and DB drifted — see README tradeoff note
        out.append({
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "url": job.url,
            "score": score,
        })
    return out


@router.get("/search")
def search(
    q: str = Query(..., min_length=1),
    mode: Literal["bm25", "vector", "hybrid"] = "hybrid",
    k: int = 20,
    db: Session = Depends(get_db),
):

    if mode == "bm25":
        ranked = bm25_search(q, k=k)
    elif mode == "vector":
        ranked = vector_search(q, k=k)
    else:
        ranked = hybrid_search(q, k=k)

    return {"query": q, "mode": mode, "results": _hydrate(db, ranked)}
