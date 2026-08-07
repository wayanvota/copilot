from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import get_db
from app.main import app
from app.models import Base, Document, DocumentVersion


def test_root_redirects_to_public_copilot():
    client = TestClient(app)
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "https://wayan.com/copilot/"


def test_chat_is_public_and_declines_without_evidence(tmp_path: Path):
    engine = create_engine(f"sqlite:///{tmp_path / 'public-chat.sqlite3'}", connect_args={"check_same_thread": False})
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)

    def override_db():
        with TestingSession() as db:
            yield db

    app.dependency_overrides[get_db] = override_db
    try:
        client = TestClient(app)
        response = client.post("/api/chat", json={"question": "Can I hire a 16-year-old to clean barns?"})
        assert response.status_code == 200
        assert response.json()["evidence_status"] == "insufficient"
    finally:
        app.dependency_overrides.clear()


def test_health_and_sources(tmp_path: Path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.sqlite3'}", connect_args={"check_same_thread": False})
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    with TestingSession() as db:
        db.add(Document(
            title="Official Test Source", agency="Nebraska DWEE", url="https://dwee.nebraska.gov/test",
            jurisdiction="Nebraska", topic="manure", source_tier=1, document_type="guidance",
            content_hash="a" * 64,
        ))
        db.commit()

    def override_db():
        with TestingSession() as db:
            yield db

    app.dependency_overrides[get_db] = override_db
    try:
        client = TestClient(app)
        health = client.get("/healthz")
        assert health.status_code == 200
        assert health.json()["corpus_documents"] == 1
        assert health.json()["jurisdiction"] == "Nebraska"
        sources = client.get("/api/sources")
        assert sources.status_code == 200
        assert sources.json()[0]["agency"] == "Nebraska DWEE"
    finally:
        app.dependency_overrides.clear()


def test_feedback_validation_rejects_unknown_rating():
    client = TestClient(app)
    response = client.post("/api/feedback", json={"answer_id": "abc", "rating": "maybe"})
    assert response.status_code == 422


def test_chat_accepts_a_structured_farm_profile(tmp_path: Path):
    engine = create_engine(f"sqlite:///{tmp_path / 'profile.sqlite3'}", connect_args={"check_same_thread": False})
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)

    def override_db():
        with TestingSession() as db:
            yield db

    app.dependency_overrides[get_db] = override_db
    try:
        client = TestClient(app)
        response = client.post("/api/chat", json={
            "question": "Do I need a construction permit?",
            "farm_context": {"county": "Madison", "operation_type": "confinement", "animal_unit_capacity": 1000},
        })
        assert response.status_code == 200
        assert response.json()["evidence_status"] == "insufficient"
    finally:
        app.dependency_overrides.clear()


def test_source_updates_only_reports_distinct_stored_versions(tmp_path: Path):
    engine = create_engine(f"sqlite:///{tmp_path / 'updates.sqlite3'}", connect_args={"check_same_thread": False})
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    with TestingSession() as db:
        document = Document(
            title="Versioned Source", agency="Nebraska DWEE", url="https://dwee.nebraska.gov/versioned",
            jurisdiction="Nebraska", topic="manure", source_tier=1, document_type="guidance", content_hash="b" * 64,
        )
        db.add(document)
        db.flush()
        db.add_all([
            DocumentVersion(document_id=document.id, content_hash="a" * 64, content="old text"),
            DocumentVersion(document_id=document.id, content_hash="b" * 64, content="new text"),
        ])
        db.commit()

    def override_db():
        with TestingSession() as db:
            yield db

    app.dependency_overrides[get_db] = override_db
    try:
        client = TestClient(app)
        response = client.get("/api/updates")
        assert response.status_code == 200
        assert response.json()[0]["version_count"] == 2
        assert response.json()[0]["title"] == "Versioned Source"
    finally:
        app.dependency_overrides.clear()
