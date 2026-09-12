from datetime import datetime, timezone

from fastapi import Response
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import main
from app.database import get_db
from app.models import Base, Bookmark, Document, DocumentVersion, Feedback
from app.schemas import Applicability, ChatResponse, Citation, CitedClaim


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)
SOURCE_ID = "11111111-1111-4111-8111-111111111111"
NOW = datetime(2026, 9, 11, 12, 0, tzinfo=timezone.utc)


def seed() -> None:
    with Session() as db:
        if db.get(Document, SOURCE_ID):
            return
        source = Document(
            id=SOURCE_ID,
            title="Nebraska Livestock Waste Control Regulations",
            agency="Nebraska DWEE",
            url="https://dwee.nebraska.gov/land-waste/agriculture/livestock-waste-control-program",
            jurisdiction="Nebraska",
            topic="permits",
            source_tier=1,
            document_type="regulation",
            content_hash="a" * 64,
            retrieved_at=NOW,
        )
        db.add(source)
        db.flush()
        db.add_all([
            DocumentVersion(document_id=SOURCE_ID, content_hash="a" * 64, content="Current version", retrieved_at=NOW),
            DocumentVersion(document_id=SOURCE_ID, content_hash="b" * 64, content="Prior version", retrieved_at=datetime(2026, 8, 1, tzinfo=timezone.utc)),
        ])
        db.commit()


seed()


def override_db():
    with Session() as db:
        yield db


def deterministic_answer(_db, request):
    if "server failure" in request.question.lower():
        raise RuntimeError("The deterministic answer service is temporarily unavailable.")
    if "<script" in request.question.lower() or "no evidence" in request.question.lower():
        return ChatResponse(
            id="22222222-2222-4222-8222-222222222222",
            conversation_id=request.conversation_id or "33333333-3333-4333-8333-333333333333",
            short_answer=[CitedClaim(text="I could not verify this from the available authoritative sources.", citations=[])],
            applicability=Applicability(level="unknown", explanation="The available source did not establish the requested claim."),
            evidence_status="insufficient",
            limitations=["A controlling source was not retrieved."],
            related_questions=["Which agency or operation detail should be checked next?"],
            citations=[],
            created_at=NOW,
        )
    context = request.farm_context
    county = context.county if context and context.county else "the stated operation"
    topic = request.topics[0] if request.topics else "permits"
    citation = Citation(
        id=SOURCE_ID,
        title="Nebraska Livestock Waste Control Regulations",
        agency="Nebraska DWEE",
        url="https://dwee.nebraska.gov/land-waste/agriculture/livestock-waste-control-program",
        retrieved_at=NOW,
        excerpt="Livestock waste facilities may require approval before construction or modification.",
    )
    return ChatResponse(
        id="22222222-2222-4222-8222-222222222222",
        conversation_id=request.conversation_id or "33333333-3333-4333-8333-333333333333",
        short_answer=[CitedClaim(text=f"Check the Nebraska approval requirement for {county} before construction.", citations=[SOURCE_ID])],
        why=[CitedClaim(text=f"The retrieved {topic} source establishes a conditional approval rule.", citations=[SOURCE_ID])],
        rules=[CitedClaim(text="Agency approval may be required before construction or modification.", citations=[SOURCE_ID])],
        documentation=[CitedClaim(text="Keep the agency approval and submitted facility plans.", citations=[SOURCE_ID])],
        related_questions=["What is the animal-unit capacity?"],
        applicability=Applicability(level="medium", explanation=f"The rule is sourced, but capacity and facility facts for {county} remain necessary."),
        evidence_status="verified",
        missing_facts=["Animal-unit capacity", "Facility type"],
        limitations=["This does not establish whether a specific permit has already been issued."],
        citations=[citation],
        created_at=NOW,
    )


main.app.dependency_overrides[get_db] = override_db
main.answer_question = deterministic_answer


@main.app.post("/__e2e/reset", include_in_schema=False)
def reset_fixture(response: Response):
    main.request_windows.clear()
    with Session() as db:
        db.query(Feedback).delete()
        db.query(Bookmark).delete()
        db.commit()
    response.headers["Cache-Control"] = "no-store"
    return {"ok": True}


app = main.app
