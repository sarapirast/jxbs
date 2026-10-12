"""
Tests the Reciprocal Rank Fusion math in hybrid_search() directly, by
stubbing out bm25_search/vector_search
"""
from app.services import hybrid_search as hs


def test_rrf_ranks_doc_present_in_both_lists_first(monkeypatch):
    monkeypatch.setattr(hs, "bm25_search", lambda q, k: [("a", 5.0), ("b", 3.0)])
    monkeypatch.setattr(hs, "vector_search", lambda q, k: [("a", 0.9), ("c", 0.7)])

    ranked_ids = [jid for jid, _ in hs.hybrid_search("query", k=10)]

    assert ranked_ids[0] == "a"  # top-ranked in both lists should win outright


def test_rrf_includes_docs_found_in_only_one_ranker(monkeypatch):
    monkeypatch.setattr(hs, "bm25_search", lambda q, k: [("a", 5.0)])
    monkeypatch.setattr(hs, "vector_search", lambda q, k: [("b", 0.9)])

    ranked_ids = {jid for jid, _ in hs.hybrid_search("query", k=10)}

    assert ranked_ids == {"a", "b"}  # union, not intersection


def test_zero_weight_effectively_disables_that_ranker(monkeypatch):
    monkeypatch.setattr(hs, "bm25_search", lambda q, k: [("a", 5.0)])
    monkeypatch.setattr(hs, "vector_search", lambda q, k: [("b", 0.9), ("a", 0.1)])

    ranked_ids = [jid for jid, _ in hs.hybrid_search("query", k=10, bm25_weight=0.0)]

    assert ranked_ids[0] == "b"  # bm25's vote is zeroed out, vector-only order wins
