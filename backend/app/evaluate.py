import argparse
import json
from pathlib import Path

from sqlalchemy.orm import Session

from .database import SessionLocal
from .retrieval import hybrid_search


def run(limit: int | None = None) -> None:
    path = Path(__file__).parents[1] / "evals" / "questions.jsonl"
    cases = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    if limit:
        cases = cases[:limit]
    passed = 0
    with SessionLocal() as db:
        for case in cases:
            results = hybrid_search(db, case["question"], [1, 2], [] )
            agencies = {result.chunk.document.agency for result in results[:5]}
            expected = set(case["expected_agencies"])
            ok = not expected or bool(agencies & expected)
            passed += int(ok)
            print(json.dumps({"id": case["id"], "passed": ok, "agencies": sorted(agencies)}))
    print(json.dumps({"retrieval_passed": passed, "total": len(cases), "rate": passed / len(cases) if cases else 0}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    run(args.limit)
