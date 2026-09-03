"""
FAISS vector index for job description embeddings
Design: IndexIDMap wrapping IndexFlatIP (inner product). Embeddings are
normalized at encode time, so inner product == cosine
similarity. FAISS ids must be int64.
"""
import hashlib
import json
import os
import faiss
import numpy as np

EMBEDDING_DIM = 768

def _stable_id(job_id: str) -> int:
    """Deterministic string -> positive int64, so re-ingesting the same
    job always maps to the same FAISS id"""
    h = hashlib.sha1(job_id.encode()).digest()
    return int.from_bytes(h[:8], byteorder="big") >> 1  # keep positive for int64


class FaissJobIndex:
    def __init__(self, index_dir: str = "data"):
        self.index_dir = index_dir
        self.index_path = os.path.join(index_dir, "faiss.index")
        self.ids_path = os.path.join(index_dir, "faiss_ids.json")
        os.makedirs(index_dir, exist_ok=True)

        self.id_to_job_id: dict[int, str] = {}
        if os.path.exists(self.index_path) and os.path.exists(self.ids_path):
            self._index = faiss.read_index(self.index_path)
            with open(self.ids_path) as f:
                self.id_to_job_id = {int(k): v for k, v in json.load(f).items()}
        else:
            flat = faiss.IndexFlatIP(EMBEDDING_DIM)
            self._index = faiss.IndexIDMap(flat)

    def add(self, job_ids: list[str], vectors: list[list[float]]) -> None:
        if not job_ids:
            return
        int_ids = np.array([_stable_id(j) for j in job_ids], dtype=np.int64)
        vecs = np.array(vectors, dtype=np.float32)
        self._index.add_with_ids(vecs, int_ids)
        for job_id, int_id in zip(job_ids, int_ids):
            self.id_to_job_id[int(int_id)] = job_id
        self.save()

    def search(self, query_vector: list[float], k: int = 20) -> list[tuple[str, float]]:
        """Returns [(job_id, cosine_similarity), ...] sorted by score descending."""
        if self._index.ntotal == 0:
            return []
        q = np.array([query_vector], dtype=np.float32)
        scores, ids = self._index.search(q, min(k, self._index.ntotal))
        results = []
        for score, int_id in zip(scores[0], ids[0]):
            if int_id == -1:
                continue
            job_id = self.id_to_job_id.get(int(int_id))
            if job_id is not None:
                results.append((job_id, float(score)))
        return results

    def save(self) -> None:
        faiss.write_index(self._index, self.index_path)
        with open(self.ids_path, "w") as f:
            json.dump({str(k): v for k, v in self.id_to_job_id.items()}, f)

    @property
    def size(self) -> int:
        return self._index.ntotal


_index_instance: FaissJobIndex | None = None


def get_index() -> FaissJobIndex:
    global _index_instance
    if _index_instance is None:
        _index_instance = FaissJobIndex()
    return _index_instance