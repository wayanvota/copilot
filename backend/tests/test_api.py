from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database import get_db
from app.main import app
from app.models import Base, Document


def test_root_redirects_to_public_copilot():
    client = TestClient(app)
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "https://wayan.com/copilot/"


def test_health_and_sources(tmp_path: Path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.sqlite3'}", connect_args={"check_same_thread": False})
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    with TestingSession() as db:
        db.add(Document(
            title="Official Test Source", agency="Iowa DNR", url="https://www.iowadnr.gov/test",
            jurisdiction="Iowa", topic="manure", source_tier=1, document_type="guidance",
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
        sources = client.get("/api/sources")
        assert sources.status_code == 200
        assert sources.json()[0]["agency"] == "Iowa DNR"
    finally:
        app.dependency_overrides.clear()


def test_feedback_validation_rejects_unknown_rating():
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {settings.app_access_token}"} if settings.app_access_token else {}
    response = client.post("/api/feedback", json={"answer_id": "abc", "rating": "maybe"}, headers=headers)
    assert response.status_code == 422
