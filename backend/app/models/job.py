from sqlalchemy import Column, String, Text, Float, DateTime, UniqueConstraint, func
from .base import Base

# Embeddings in a FAISS index: holds vectors
EMBEDDING_DIM = 384


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True)  # f"{source}:{source_job_id}"
    source = Column(String, nullable=False)
    source_job_id = Column(String, nullable=False)
    # normalized "title|company|location" — catches the same posting
    # showing up on two different sources
    dedup_key = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    location = Column(String, nullable=True)
    description = Column(Text, nullable=False)
    url = Column(String, nullable=True)
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    employment_type = Column(String, nullable=True)
    posted_at = Column(String, nullable=True)
    ingested_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("source", "source_job_id", name="uq_source_job"),
    )
