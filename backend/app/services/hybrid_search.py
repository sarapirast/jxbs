"""
Hybrid retrieval: combines BM25 (keyword) and FAISS (semantic) rankings
via Reciprocal Rank Fusion. Score(doc) = sum over each ranker of  1 / (k_rrf + rank_in_that_list)
Doc missing from a list contributes 0 for that list..
"""
from .bm25_index import get_bm25_index
from .vector_index import get_index
from .embeddings import embed_query

RRF_K = 60


def bm25_search(query: str, k: int = 20) -> list[tuple[str, float]]:
    return get_bm25_index().search(query, k=k)


def vector_search(query: str, k: int = 20) -> list[tuple[str, float]]:
    query_vec = embed_query(query)  # NOT embed_text() — see embeddings.py docstring
    return get_index().search(query_vec, k=k)


def hybrid_search(
    query: str,
    k: int = 20,
    candidate_pool: int = 50,
    bm25_weight: float = 1.0,
    vector_weight: float = 1.0,
) -> list[tuple[str, float]]:

    bm25_results = bm25_search(query, k=candidate_pool)
    vector_results = vector_search(query, k=candidate_pool)

    rrf_scores: dict[str, float] = {}
    for rank, (job_id, _) in enumerate(bm25_results):
        rrf_scores[job_id] = rrf_scores.get(job_id, 0.0) + bm25_weight / (RRF_K + rank + 1)
    for rank, (job_id, _) in enumerate(vector_results):
        rrf_scores[job_id] = rrf_scores.get(job_id, 0.0) + vector_weight / (RRF_K + rank + 1)

    ranked = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    return ranked[:k]