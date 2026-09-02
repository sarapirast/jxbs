from fastapi import FastAPI
from .routes import ingest

app = FastAPI(title="Jinder-solo API")

app.include_router(ingest.router)


@app.get("/health")
def health():
    return {"status": "ok"}
