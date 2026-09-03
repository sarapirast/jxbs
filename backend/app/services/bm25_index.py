"""
BM25 keyword index — the "keyword" half of hybrid search, paired with
FAISS's semantic half (see vector_index.py).
"""
import os
import pickle
import re
from rank_bm25 import BM25Okapi

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


class BM25JobIndex:
    def __init__(self, index_dir: str = "data"):
        self.path = os.path.join(index_dir, "bm25.pkl")
        os.makedirs(index_dir, exist_ok=True)
        self.job_ids: list[str] = []
        self._bm25: BM25Okapi | None = None
        if os.path.exists(self.path):
            with open(self.path, "rb") as f:
                self.job_ids, self._bm25 = pickle.load(f)

    def rebuild(self, job_ids: list[str], texts: list[str]) -> None:
        """BM25 doesn't support incremental add — rebuild from the full
        corpus each time"""
        tokenized = [tokenize(t) for t in texts]
        self._bm25 = BM25Okapi(tokenized)
        self.job_ids = job_ids
        self.save()

    def search(self, query: str, k: int = 20) -> list[tuple[str, float]]:
        if self._bm25 is None or not self.job_ids:
            return []
        scores = self._bm25.get_scores(tokenize(query))
        ranked = sorted(zip(self.job_ids, scores), key=lambda x: x[1], reverse=True)
        return [(jid, float(s)) for jid, s in ranked[:k] if s > 0]

    def save(self) -> None:
        with open(self.path, "wb") as f:
            pickle.dump((self.job_ids, self._bm25), f)

    @property
    def size(self) -> int:
        return len(self.job_ids)


_bm25_instance: BM25JobIndex | None = None


def get_bm25_index() -> BM25JobIndex:
    global _bm25_instance
    if _bm25_instance is None:
        _bm25_instance = BM25JobIndex()
    return _bm25_instance
