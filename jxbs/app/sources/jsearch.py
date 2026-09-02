import os
import httpx
from .base import JobSource, NormalizedJob

BASE_URL = "https://jsearch.p.rapidapi.com/search"


class JSearchSource(JobSource):
    name = "jsearch"

    def __init__(self):
        self.api_key = os.environ.get("RAPIDAPI_KEY")
        if not self.api_key:
            raise RuntimeError(
                "RAPIDAPI_KEY not set. Subscribe to JSearch on RapidAPI and "
                "add the key to your .env"
            )

    def fetch(self, query: str, location: str, max_results: int = 50) -> list[NormalizedJob]:
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
        }
        params = {
            "query": f"{query} in {location}",
            "page": "1",
            "num_pages": str(max(1, max_results // 10)),  # ~10 results/page
        }
        resp = httpx.get(BASE_URL, headers=headers, params=params, timeout=15.0)
        resp.raise_for_status()
        data = resp.json()

        jobs = []
        for item in data.get("data", [])[:max_results]:
            jobs.append(NormalizedJob(
                source=self.name,
                source_job_id=str(item.get("job_id")),
                title=(item.get("job_title") or "").strip(),
                company=item.get("employer_name") or "Unknown",
                location=item.get("job_city") or item.get("job_country"),
                description=(item.get("job_description") or "").strip(),
                url=item.get("job_apply_link"),
                salary_min=item.get("job_min_salary"),
                salary_max=item.get("job_max_salary"),
                employment_type=item.get("job_employment_type"),
                posted_at=item.get("job_posted_at_datetime_utc"),
            ))
        return jobs
