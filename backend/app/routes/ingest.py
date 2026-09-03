from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..models.base import get_db
from ..services.ingest import run_ingest

router = APIRouter()


class IngestRequest(BaseModel):
    queries: list[str] = ["software engineer", "machine learning engineer", "data scientist"]
    locations: list[str] = ["San Francisco, CA", "Seattle, WA", "New York, NY", "Remote"]
    max_results_per_query: int = 25


@router.post("/ingest")
def trigger_ingest(req: IngestRequest, db: Session = Depends(get_db)):
    """
    Manually triggered pull. Safe to call repeatedly: dedup happens both within the
    batch and against what's already stored.
    """
    return run_ingest(db, req.queries, req.locations, req.max_results_per_query)
