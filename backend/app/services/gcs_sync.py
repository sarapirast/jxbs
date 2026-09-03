"""
Backs up and restores the FAISS index, BM25 pickle, AND a Postgres dump
to/from Google Cloud Storage — so all state survives the VM being
replaced.

Only active when GCS_BUCKET is set in the environment.
"""

import os
import subprocess
from google.cloud import storage
from google.cloud.exceptions import NotFound

INDEX_DIR = "data"
INDEX_FILES = ["faiss.index", "faiss_ids.json", "bm25.pkl"]
DB_DUMP_PATH = os.path.join(INDEX_DIR, "postgres_dump.sql")


def _get_bucket_name():
    return os.environ.get("GCS_BUCKET")


def _get_client():
    return storage.Client()


def backup_index_to_gcs() -> dict:
    bucket_name = _get_bucket_name()
    if not bucket_name:
        return {"skipped": "GCS_BUCKET not set — local dev, nothing to do"}

    client = _get_client()
    bucket = client.bucket(bucket_name)
    uploaded = []
    for fname in INDEX_FILES:
        local_path = os.path.join(INDEX_DIR, fname)
        if os.path.exists(local_path):
            blob = bucket.blob(f"index/{fname}")
            blob.upload_from_filename(local_path)
            uploaded.append(fname)
    return {"bucket": bucket_name, "uploaded": uploaded}


def restore_index_from_gcs() -> dict:
    bucket_name = _get_bucket_name()
    if not bucket_name:
        return {"skipped": "GCS_BUCKET not set — local dev, nothing to do"}

    os.makedirs(INDEX_DIR, exist_ok=True)
    client = _get_client()
    bucket = client.bucket(bucket_name)
    restored = []
    missing = []
    for fname in INDEX_FILES:
        local_path = os.path.join(INDEX_DIR, fname)
        blob = bucket.blob(f"index/{fname}")
        try:
            blob.download_to_filename(local_path)
            restored.append(fname)
        except NotFound:
            # Normal on first-ever deploy — nothing backed up yet.
            missing.append(fname)
    return {"bucket": bucket_name, "restored": restored, "missing": missing}


def backup_postgres_to_gcs(database_url: str) -> dict:
    """Runs pg_dump against DATABASE_URL, uploads the .sql file to GCS."""
    bucket_name = _get_bucket_name()
    if not bucket_name:
        return {"skipped": "GCS_BUCKET not set — local dev, nothing to do"}

    os.makedirs(INDEX_DIR, exist_ok=True)
    result = subprocess.run(
        ["pg_dump", database_url, "-f", DB_DUMP_PATH],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return {"error": f"pg_dump failed: {result.stderr}"}

    client = _get_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob("db/postgres_dump.sql")
    blob.upload_from_filename(DB_DUMP_PATH)
    return {"bucket": bucket_name, "uploaded": "postgres_dump.sql"}


def restore_postgres_from_gcs(database_url: str) -> dict:
    """Downloads the latest dump from GCS and restores it via psql."""
    bucket_name = _get_bucket_name()
    if not bucket_name:
        return {"skipped": "GCS_BUCKET not set — local dev, nothing to do"}

    os.makedirs(INDEX_DIR, exist_ok=True)
    client = _get_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob("db/postgres_dump.sql")
    try:
        blob.download_to_filename(DB_DUMP_PATH)
    except NotFound:
        return {"bucket": bucket_name, "missing": "postgres_dump.sql"}

    result = subprocess.run(
        ["psql", database_url, "-f", DB_DUMP_PATH],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return {"error": f"psql restore failed: {result.stderr}"}
    return {"bucket": bucket_name, "restored": "postgres_dump.sql"}
