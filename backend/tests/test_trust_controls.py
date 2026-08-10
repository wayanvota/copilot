from datetime import datetime, timezone

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from app.copilot import _clean_claim_text, _farm_context, _strict_response_schema, _validate_citations
from app.ingest import _allowed_url, chunk_text, ingest_source, read_manual_source, sync_registry
from app.models import Base, Chunk, Document
from app.retrieval import _expand_query, hybrid_search
from app.schemas import Applicability, CitedClaim, FarmContext, GeneratedAnswer
from app.source_registry import APPROVED_SOURCES


def answer_with(citation: str) -> GeneratedAnswer:
    return GeneratedAnswer(
        short_answer=[CitedClaim(text="A test claim.", citations=[citation])],
        why=[], rules=[], documentation=[], related_questions=[],
        applicability=Applicability(level="high", explanation="The facts match."),
        evidence_status="verified", limitations=[],
    )


def test_unretrieved_citation_withholds_answer():
    answer = _validate_citations(answer_with("invented"), {"S1": "retrieved"})
    assert answer.evidence_status == "insufficient"
    assert answer.short_answer[0].citations == []
    assert "could not verify" in answer.short_answer[0].text.lower()


def test_uncited_claim_is_omitted_without_discarding_cited_answer():
    answer = answer_with("S1")
    answer.rules.append(CitedClaim(text="Unsupported extra claim.", citations=[]))
    checked = _validate_citations(answer, {"S1": "retrieved"})
    assert checked.evidence_status == "verified"
    assert checked.short_answer[0].citations == ["retrieved"]
    assert checked.rules == []


def test_chunk_ids_are_removed_from_visible_claim_text():
    chunk_id = "d9ad2ec5-2bf8-4edc-8fd0-9e0f4c65e755"
    assert _clean_claim_text(f"A cited rule applies [{chunk_id}].") == "A cited rule applies."
    leaked = (
        'A cited rule applies. ["d9ad2ec5-2bf8-4edc-8fd0-9e0f4c65e755",'
        '"affbff8a-64ce-445a-a500-9b2c686c23bc"]},{'
    )
    assert _clean_claim_text(leaked) == "A cited rule applies."
    assert _clean_claim_text("A cited rule applies. 【】") == "A cited rule applies."
    assert _clean_claim_text("A cited rule applies [S1, S2].") == "A cited rule applies."


def test_farm_context_is_explicitly_labeled_as_user_context():
    context = FarmContext(county="Madison", operation_type="confinement", animal_unit_capacity=1000)
    rendered = _farm_context(context)
    assert "county: Madison" in rendered
    assert "operation type: confinement" in rendered


def test_response_schema_requires_every_declared_property():
    schema = _strict_response_schema(["S1", "S2"])

    def check(node: object) -> None:
        if isinstance(node, dict):
            properties = node.get("properties")
            if isinstance(properties, dict):
                assert node["required"] == list(properties)
                assert node["additionalProperties"] is False
            for value in node.values():
                check(value)
        elif isinstance(node, list):
            for value in node:
                check(value)

    check(schema)
    citation_items = schema["$defs"]["CitedClaim"]["properties"]["citations"]["items"]
    assert citation_items["enum"] == ["S1", "S2"]


def test_approved_source_hosts_only():
    assert _allowed_url("https://dwee.nebraska.gov/land-waste/agriculture/livestock-waste-control-program")
    assert _allowed_url("https://nda.nebraska.gov/animal/reporting")
    assert _allowed_url("https://subdomain.aphis.usda.gov/example")
    assert not _allowed_url("http://dwee.nebraska.gov/insecure")
    assert not _allowed_url("https://dwee.nebraska.gov.evil.example/phishing")
    assert not _allowed_url("https://example.com/blog")


def test_chunking_preserves_content_and_limits_size():
    text = "\n\n".join(f"Paragraph {i} " + ("evidence " * 80) for i in range(12))
    chunks = chunk_text(text, size=900, overlap=100)
    assert len(chunks) > 1
    assert all(len(chunk) <= 900 for chunk in chunks)


def test_manual_nebraska_sources_contain_controlling_text():
    expected = {
        "corpus/manual/nebraska-title-130.pdf": "LIVESTOCK WASTE CONTROL REGULATIONS",
        "corpus/manual/nebraska-discharge-notification.pdf": "24 hours",
        "corpus/manual/nebraska-reportable-disease-list.pdf": "Porcine Reproductive and Respiratory Syndrome",
        "corpus/manual/nebraska-employment-minors.pdf": "Employment Certificate",
    }
    for path, phrase in expected.items():
        assert phrase.lower() in read_manual_source(path).lower()


def test_every_registered_manual_pdf_has_extractable_text():
    manual_sources = [source for source in APPROVED_SOURCES if source.get("manual_path")]
    assert len(manual_sources) >= 10
    for source in manual_sources:
        assert len(read_manual_source(source["manual_path"])) > 200, source["title"]


def test_manual_source_replaces_existing_chunks(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'replacement.sqlite3'}")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    source = next(item for item in APPROVED_SOURCES if item["title"].startswith("Title 130"))
    monkeypatch.setattr("app.ingest.embed_texts", lambda texts: [[0.0] * 1024 for _ in texts])
    with Session() as db:
        document = Document(title=source["title"], agency=source["agency"], url=source["url"], jurisdiction="Nebraska", topic="manure", source_tier=1, document_type="regulation", content_hash="old")
        db.add(document)
        db.flush()
        db.add(Chunk(document_id=document.id, ordinal=0, content="Old fallback", token_count=3, embedding=[0.0] * 1024))
        db.commit()
        ingest_source(db, source)
        db.commit()
        assert db.scalar(select(func.count(Chunk.id)).where(Chunk.document_id == document.id)) > 1


def test_registry_sync_removes_unapproved_jurisdiction_documents(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'sync.sqlite3'}")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    approved = APPROVED_SOURCES[0]
    with Session() as db:
        db.add_all([
            Document(title=approved["title"], agency=approved["agency"], url=approved["url"], jurisdiction="Nebraska", topic="permits", source_tier=1, document_type="guidance", content_hash="a"),
            Document(title="Old jurisdiction source", agency="Old agency", url="https://example.invalid/old", jurisdiction="Other", topic="permits", source_tier=1, document_type="guidance", content_hash="b"),
        ])
        db.commit()
        assert sync_registry(db) == 1
        assert db.scalar(select(func.count(Document.id))) == 1


def test_nebraska_query_expansion_uses_canonical_terms():
    acreage, _ = _expand_query("How many acres do I need for pig manure?")
    assert "Nebraska nutrient management plan" in acreage
    prrs, _ = _expand_query("Is PRRS legally reportable in Nebraska?")
    assert "Porcine reproductive and respiratory syndrome" in prrs
    construction, _ = _expand_query("What separation distances apply to a new Nebraska hog barn near a well?")
    assert "Nebraska Title 130" in construction
    discharge, _ = _expand_query("How soon must I report a manure spill into a stream?")
    assert "within 24 hours" in discharge


def test_manure_acreage_query_prioritizes_land_requirement_evidence(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'retrieval.sqlite3'}")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    monkeypatch.setattr("app.retrieval.embed_texts", lambda texts: [[0.0] * 1024 for _ in texts])
    with Session() as db:
        land = Document(title="Manure Nutrient Production and Land Requirements", agency="Nebraska Extension", url="https://water.unl.edu/manure/nutrient-production/", jurisdiction="Nebraska", topic="manure", source_tier=2, document_type="extension guidance", content_hash="land")
        other = Document(title="Livestock Waste Control Program", agency="Nebraska DWEE", url="https://dwee.nebraska.gov/example", jurisdiction="Nebraska", topic="manure", source_tier=2, document_type="guidance", content_hash="other")
        db.add_all([land, other]); db.flush()
        db.add_all([
            Chunk(document_id=land.id, ordinal=0, content="Calculate sufficient acres from annual manure nutrients, planned application rate, crop needs, and soil tests.", token_count=20, embedding=[0.0] * 1024),
            Chunk(document_id=other.id, ordinal=0, content="Livestock waste facilities require inspection.", token_count=8, embedding=[0.0] * 1024),
        ]); db.commit()
        results = hybrid_search(db, "How much land do I need to spread manure from my pigs?", [2], ["manure"])
        assert results[0].chunk.document_id == land.id
