"""
Scores bm25 / vector / hybrid retrieval against eval/eval_set.json,
reporting Recall@5 and Recall@10 for each mode.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.base import SessionLocal
from app.models.job import Job
from app.services.hybrid_search import bm25_search, vector_search, hybrid_search

EVAL_SET_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "eval", "eval_set.json")


def resolve_relevant_ids(db, bare_ids: list[str]) -> set[str]:
    if not bare_ids:
        return set()
    rows = db.query(Job.id).filter(Job.source_job_id.in_(bare_ids)).all()
    return {r.id for r in rows}


def recall_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    if not relevant:
        return None  # undefined for negative-control queries with 0 relevant docs
    top_k = set(retrieved[:k])
    return len(top_k & relevant) / len(relevant)


def main():
    with open(EVAL_SET_PATH) as f:
        eval_set = [row for row in json.load(f) if row.get("query")]

    print(f"Scoring {len(eval_set)} queries across bm25 / vector / hybrid...\n")

    db = SessionLocal()
    modes = {
        "bm25": lambda q, k: [jid for jid, _ in bm25_search(q, k=k)],
        "vector": lambda q, k: [jid for jid, _ in vector_search(q, k=k)],
        "hybrid": lambda q, k: [jid for jid, _ in hybrid_search(q, k=k)],
    }

    # per-mode, per-k running totals
    totals = {mode: {5: [], 10: []} for mode in modes}

    for row in eval_set:
        relevant = resolve_relevant_ids(db, row["relevant_job_ids"])
        print(f"Query: {row['query']!r}  ({len(relevant)} relevant)")
        for mode, fn in modes.items():
            retrieved = fn(row["query"], 10)
            r5 = recall_at_k(retrieved, relevant, 5)
            r10 = recall_at_k(retrieved, relevant, 10)
            if r5 is not None:
                totals[mode][5].append(r5)
                totals[mode][10].append(r10)
            print(f"  {mode:8s}  Recall@5={r5}  Recall@10={r10}")
        print()

    db.close()

    print("=" * 50)
    print(f"{'Mode':10s} {'Recall@5':>10s} {'Recall@10':>10s}  (n queries with ground truth)")
    for mode in modes:
        r5s, r10s = totals[mode][5], totals[mode][10]
        avg5 = sum(r5s) / len(r5s) if r5s else float("nan")
        avg10 = sum(r10s) / len(r10s) if r10s else float("nan")
        print(f"{mode:10s} {avg5:10.3f} {avg10:10.3f}  (n={len(r5s)})")


if __name__ == "__main__":
    main()
