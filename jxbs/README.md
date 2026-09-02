# Jxbs — backend

## Setup

1. Postgres.
2. `cp .env.example .env` — fill in `DATABASE_URL` and at least one of
   `ADZUNA_APP_ID`/`ADZUNA_APP_KEY` (developer.adzuna.com) or
   `RAPIDAPI_KEY` (rapidapi.com, JSearch).
3. `pip install -r requirements.txt`
4. Create the `jobs` table (`Base.metadata.create_all(engine)`, or add Alembic).
5. `uvicorn app.main:app --reload`

FAISS index files (`data/faiss.index`, `data/faiss_ids.json`) are created
on first ingest. Put `data/` on a persistent volume if deploying to
ephemeral disk.

## Pulling fresh postings

Manual trigger, no scheduler:

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"queries": ["software engineer", "machine learning engineer"], "locations": ["Remote", "San Francisco, CA"]}'
```

Returns fetched/unique/new counts. Safe to call repeatedly. Missing API
key for a source just skips that source.

## Architecture notes

- **Adapter pattern** (`app/sources/`): new source = one file + one registry line.
- **Cross-source dedup** (`ingest.py::_normalize_key`): same posting from
  two sources collapses to one record.
- **Local embeddings** (`all-MiniLM-L6-v2`): no per-call cost, runs locally.