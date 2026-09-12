"""One-request, opt-in smoke for the Copilot's structured OpenAI contract."""

from datetime import datetime, timezone

from app.copilot import _generate, _validate_citations
from app.embeddings import get_client
from app.models import Chunk, Document
from app.retrieval import RetrievedChunk
from app.schemas import FarmContext


def main() -> None:
    document = Document(
        id="11111111-1111-4111-8111-111111111111",
        title="Synthetic Nebraska Permit Rule",
        agency="Nebraska test agency",
        url="https://example.org/nebraska-permit-rule",
        jurisdiction="Nebraska",
        topic="permits",
        source_tier=1,
        document_type="regulation",
        content_hash="a" * 64,
        retrieved_at=datetime.now(timezone.utc),
    )
    chunk = Chunk(
        id="22222222-2222-4222-8222-222222222222",
        document=document,
        ordinal=0,
        content=(
            "A producer must obtain written agency approval before constructing "
            "a new livestock waste control facility. This synthetic excerpt is "
            "only for validating the structured evidence boundary."
        ),
        token_count=31,
        embedding=[0.0] * 1024,
    )
    results = [RetrievedChunk(chunk=chunk, score=1.0)]
    aliases = {"S1": chunk.id}
    generated = _generate(
        get_client(),
        "What must I do before constructing this facility?",
        "No prior conversation.",
        results,
        "33333333-3333-4333-8333-333333333333",
        FarmContext(county="Madison", operation_type="confinement"),
        aliases,
    )
    checked = _validate_citations(generated, aliases)
    assert checked.evidence_status in {"verified", "conflicting"}
    assert checked.short_answer
    assert all(claim.citations == [chunk.id] for claim in checked.short_answer)
    print("PASS structured OpenAI evidence boundary accepted one synthetic source")


if __name__ == "__main__":
    main()
