from datetime import datetime, timezone
from types import SimpleNamespace

from app.copilot import _strict_response_schema, _validate_citations
from app.ingest import _allowed_url, chunk_text
from app.schemas import Applicability, CitedClaim, GeneratedAnswer


def answer_with(citation: str) -> GeneratedAnswer:
    return GeneratedAnswer(
        short_answer=[CitedClaim(text="A test claim.", citations=[citation])],
        why=[], rules=[], documentation=[], related_questions=[],
        applicability=Applicability(level="high", explanation="The facts match."),
        evidence_status="verified", limitations=[],
    )


def test_unretrieved_citation_withholds_answer():
    answer = _validate_citations(answer_with("invented"), {"retrieved"})
    assert answer.evidence_status == "insufficient"
    assert answer.short_answer[0].citations == []
    assert "could not verify" in answer.short_answer[0].text.lower()


def test_verified_claim_must_have_citation():
    answer = answer_with("retrieved")
    answer.short_answer[0].citations = []
    checked = _validate_citations(answer, {"retrieved"})
    assert checked.evidence_status == "insufficient"


def test_uncited_claim_is_omitted_without_discarding_cited_answer():
    answer = answer_with("retrieved")
    answer.rules.append(CitedClaim(text="Unsupported extra claim.", citations=[]))
    checked = _validate_citations(answer, {"retrieved"})
    assert checked.evidence_status == "verified"
    assert checked.short_answer[0].text == "A test claim."
    assert checked.rules == []
    assert "1 uncited" in checked.limitations[-1]


def test_response_schema_requires_every_declared_property():
    schema = _strict_response_schema()

    def assert_strict_objects(node: object) -> None:
        if isinstance(node, dict):
            properties = node.get("properties")
            if isinstance(properties, dict):
                assert node["required"] == list(properties)
                assert node["additionalProperties"] is False
            for value in node.values():
                assert_strict_objects(value)
        elif isinstance(node, list):
            for value in node:
                assert_strict_objects(value)

    assert_strict_objects(schema)


def test_approved_source_hosts_only():
    assert _allowed_url("https://www.iowadnr.gov/environmental-protection")
    assert _allowed_url("https://subdomain.aphis.usda.gov/example")
    assert not _allowed_url("http://www.iowadnr.gov/insecure")
    assert not _allowed_url("https://iowadnr.gov.evil.example/phishing")
    assert not _allowed_url("https://example.com/blog")


def test_chunking_preserves_content_and_limits_size():
    text = "\n\n".join(f"Paragraph {i} " + ("evidence " * 80) for i in range(12))
    chunks = chunk_text(text, size=900, overlap=100)
    assert len(chunks) > 1
    assert all(len(chunk) <= 900 for chunk in chunks)
    assert "Paragraph 0" in chunks[0]
