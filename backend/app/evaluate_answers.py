"""Run the Nebraska benchmark through the complete retrieval and answer pipeline."""

import argparse
import json
import time
from pathlib import Path

from .copilot import answer_question
from .database import SessionLocal
from .schemas import ChatRequest


def run(limit: int | None = None, ids: set[str] | None = None) -> None:
    path = Path(__file__).parents[1] / "evals" / "questions.jsonl"
    cases = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    if ids:
        cases = [case for case in cases if case["id"] in ids]
    if limit:
        cases = cases[:limit]

    results: list[dict] = []
    with SessionLocal() as db:
        for case in cases:
            started = time.perf_counter()
            try:
                answer = answer_question(
                    db,
                    ChatRequest(
                        question=case["question"],
                        source_tiers=[1, 2],
                        topics=[case["topic"]],
                    ),
                )
                result = {
                    "id": case["id"],
                    "evidence_status": answer.evidence_status,
                    "applicability": answer.applicability.level,
                    "citation_count": len(answer.citations),
                    "claim_count": len(answer.short_answer) + len(answer.why) + len(answer.rules) + len(answer.documentation),
                    "missing_fact_count": len(answer.missing_facts),
                    "latency_ms": round((time.perf_counter() - started) * 1000),
                    "agencies": sorted({citation.agency for citation in answer.citations}),
                    "short_answer": " ".join(claim.text for claim in answer.short_answer),
                    "limitations": answer.limitations,
                }
            except Exception as exc:
                db.rollback()
                result = {
                    "id": case["id"],
                    "error": type(exc).__name__,
                    "latency_ms": round((time.perf_counter() - started) * 1000),
                }
            results.append(result)
            print(json.dumps(result), flush=True)

    completed = [item for item in results if "error" not in item]
    verified = [item for item in completed if item["evidence_status"] == "verified"]
    summary = {
        "total": len(results),
        "completed": len(completed),
        "verified": len(verified),
        "insufficient": sum(item.get("evidence_status") == "insufficient" for item in completed),
        "conflicting": sum(item.get("evidence_status") == "conflicting" for item in completed),
        "with_citations": sum(item.get("citation_count", 0) > 0 for item in completed),
        "median_latency_ms": sorted(item["latency_ms"] for item in completed)[len(completed) // 2] if completed else None,
    }
    print(json.dumps({"summary": summary}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int)
    parser.add_argument("--ids", help="Comma-separated benchmark IDs")
    args = parser.parse_args()
    run(args.limit, set(args.ids.split(",")) if args.ids else None)
