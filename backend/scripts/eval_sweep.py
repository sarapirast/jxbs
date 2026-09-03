"""
Sweeps bm25_weight/vector_weight combinations for hybrid_search against
eval/eval_set.json, so you can find the best-performing weighting in one
run instead of re-running eval_search.py once per config by hand.

Usage:
    python scripts/eval_sweep.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app.models.base import SessionLocal
from app.models.job import Job
from app.services.hybrid_search import hybrid_search, bm25_search
from scripts.eval_search import resolve_relevant_ids, recall_at_k, EVAL_SET_PATH

# Weight combos to try. (1.0, 1.0) = plain RRF, same as before — included
# as a baseline so the sweep table shows whether weighting actually helps.
WEIGHT_CONFIGS = [
    (1.0, 1.0),   # plain RRF (baseline, same as eval_search.py's hybrid mode)
    (1.5, 1.0),
    (2.0, 1.0),
    (3.0, 1.0),
    (1.0, 0.5),
    (1.0, 0.0),   # equivalent to bm25-only, sanity check upper bound
]


def main():
    with open(EVAL_SET_PATH) as f:
        eval_set = [row for row in json.load(f) if row.get("query")]

    db = SessionLocal()

    print(f"Sweeping {len(WEIGHT_CONFIGS)} weight configs over {len(eval_set)} queries...\n")
    print(f"{'bm25_w':>7} {'vec_w':>7} {'Recall@5':>10} {'Recall@10':>10}")

    for bm25_w, vec_w in WEIGHT_CONFIGS:
        r5s, r10s = [], []
        for row in eval_set:
            relevant = resolve_relevant_ids(db, row["relevant_job_ids"])
            if not relevant:
                continue
            retrieved = [jid for jid, _ in hybrid_search(row["query"], k=10, bm25_weight=bm25_w, vector_weight=vec_w)]
            r5 = recall_at_k(retrieved, relevant, 5)
            r10 = recall_at_k(retrieved, relevant, 10)
            r5s.append(r5)
            r10s.append(r10)
        avg5 = sum(r5s) / len(r5s)
        avg10 = sum(r10s) / len(r10s)
        print(f"{bm25_w:7.1f} {vec_w:7.1f} {avg5:10.3f} {avg10:10.3f}")

    db.close()
    print("\nPick whichever (bm25_weight, vector_weight) scores best, then hardcode")
    print("those values as the defaults in hybrid_search()'s signature — or expose")
    print("them as query params on the /search route if you want them adjustable live.")


if __name__ == "__main__":
    main()
