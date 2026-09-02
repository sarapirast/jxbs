"""
Adzuna adapter. Docs: https://developer.adzuna.com/docs/search
"""
import os
import httpx
from .base import JobSource, NormalizedJob

BASE_URL = "https://api.adzuna.com/v1/api/jobs/us/search/1"


class AdzunaSource(JobSource):
    name = "adzuna"

    def __init__(self):
        self.app_id = os.environ.get("ADZUNA_APP_ID")
        self.app_key = os.environ.get("ADZUNA_APP_KEY")
        if not self.app_id or not self.app_key:
            raise RuntimeError(
                "ADZUNA_APP_ID / ADZUNA_APP_KEY not set. "
                "Register at https://developer.adzuna.com and add them to your .env"
            )

    def fetch(self, query: str, location: str, max_results: int = 50) -> list[NormalizedJob]:
        params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "what": query,
            "where": location,
            "results_per_page": min(max_results, 50),  # Adzuna caps at 50/page
            "content-type": "application/json",
        }
        resp = httpx.get(BASE_URL, params=params, timeout=15.0)
        resp.raise_for_status()
        data = resp.json()

        jobs = []
        for item in data.get("results", []):
            jobs.append(NormalizedJob(
                source=self.name,
                source_job_id=str(item.get("id")),
                title=item.get("title", "").strip(),
                company=(item.get("company") or {}).get("display_name", "Unknown"),
                location=(item.get("location") or {}).get("display_name"),
                description=item.get("description", "").strip(),
                url=item.get("redirect_url"),
                salary_min=item.get("salary_min"),
                salary_max=item.get("salary_max"),
                employment_type=item.get("contract_time"),
                posted_at=item.get("created"),
            ))
        return jobs
