from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

from ..models.base import get_db
from ..services.resume_matcher import extract_text_from_pdf, extract_skills, build_query_from_skills
from ..services.hybrid_search import hybrid_search
from .search import _hydrate

router = APIRouter()


@router.post("/match-resume")
async def match_resume(file: UploadFile = File(...), k: int = 10, db: Session = Depends(get_db)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    file_bytes = await file.read()
    try:
        resume_text = extract_text_from_pdf(file_bytes)
    except Exception:
        raise HTTPException(status_code=400, detail="Couldn't read this PDF — is it a valid, non-scanned PDF?")

    if not resume_text.strip():
        raise HTTPException(
            status_code=400,
            detail="No extractable text found. Scanned/image-only PDFs aren't supported — try a PDF exported directly from a text editor.",
        )

    skills = extract_skills(resume_text)
    if not skills:
        return {
            "skills_detected": [],
            "results": [],
            "note": "No known skills detected in this resume — the keyword list may not cover your specific stack.",
        }

    query = build_query_from_skills(skills)
    ranked = hybrid_search(query, k=k)

    return {
        "skills_detected": skills,
        "query_used": query,
        "results": _hydrate(db, ranked),
    }