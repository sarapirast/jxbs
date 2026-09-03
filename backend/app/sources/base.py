from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class NormalizedJob:
    source: str            # "adzuna" | "jsearch" | "linkedin_bulk" | "indeed_live"
    source_job_id: str      # id as given by the source, used for dedup within a source
    title: str
    company: str
    location: Optional[str]
    description: str
    url: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    employment_type: Optional[str] = None
    posted_at: Optional[str] = None  # ISO date string if the source provides one


class JobSource(ABC):
    """Base class every job-source adapter implements."""

    name: str  # short identifier, e.g. "adzuna"

    @abstractmethod
    def fetch(self, query: str, location: str, max_results: int = 50) -> list[NormalizedJob]:
        """
        Fetch job postings matching `query` near `location`.
        """
        raise NotImplementedError
