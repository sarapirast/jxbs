import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import ingest, search, resume_match
from .services.gcs_sync import restore_index_from_gcs, restore_postgres_from_gcs

app = FastAPI(title="jxbs API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router)
app.include_router(search.router)
app.include_router(resume_match.router)


@app.on_event("startup")
def startup_restore():
    # No-op locally (GCS_BUCKET unset)
    index_result = restore_index_from_gcs()
    print(f"[startup] index restore: {index_result}")
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        db_result = restore_postgres_from_gcs(db_url)
        print(f"[startup] postgres restore: {db_result}")


@app.get("/health")
def health():
    return {"status": "ok"}
