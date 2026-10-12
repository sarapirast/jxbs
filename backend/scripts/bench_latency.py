"""
Times /search requests against a running JXBS instance and reports
p50/p95/p99 latency.

Requires the server to already be running with some data ingested
"""
import argparse
import time

import httpx

DEFAULT_QUERIES = [
    "software engineer", "machine learning engineer", "data scientist",
    "backend developer", "site reliability engineer", "data analyst",
    "frontend engineer", "devops engineer",
]


def percentile(values: list[float], pct: float) -> float:
    values = sorted(values)
    idx = min(int(len(values) * pct), len(values) - 1)
    return values[idx]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--n", type=int, default=50, help="number of requests to time")
    parser.add_argument("--mode", default="hybrid", choices=["bm25", "vector", "hybrid"])
    args = parser.parse_args()

    durations_ms = []
    with httpx.Client(timeout=30) as client:
        # Warmup request — excludes first-connection/cold-cache overhead from the numbers.
        client.get(f"{args.url}/search", params={"q": DEFAULT_QUERIES[0], "mode": args.mode})

        for i in range(args.n):
            query = DEFAULT_QUERIES[i % len(DEFAULT_QUERIES)]
            start = time.perf_counter()
            resp = client.get(f"{args.url}/search", params={"q": query, "mode": args.mode})
            elapsed_ms = (time.perf_counter() - start) * 1000
            resp.raise_for_status()
            durations_ms.append(elapsed_ms)

    print(f"Timed {args.n} requests against {args.url}/search (mode={args.mode})\n")
    print(f"  p50: {percentile(durations_ms, 0.50):.1f} ms")
    print(f"  p95: {percentile(durations_ms, 0.95):.1f} ms")
    print(f"  p99: {percentile(durations_ms, 0.99):.1f} ms")
    print(f"  min: {min(durations_ms):.1f} ms")
    print(f"  max: {max(durations_ms):.1f} ms")


if __name__ == "__main__":
    main()
