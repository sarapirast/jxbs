from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from .routes import ingest, search

app = FastAPI(title="Jinder-solo API")

app.include_router(ingest.router)
app.include_router(search.router)

@app.get("/health")
def health():
    return {"status": "ok"}
