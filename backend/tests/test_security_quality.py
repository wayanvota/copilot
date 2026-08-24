import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from app.database import get_db
from app.ingest import _allowed_url, read_manual_source
from app.main import MAX_REQUEST_BODY_BYTES, app, request_windows
from app.models import Base, Bookmark, Conversation, Feedback, Message


@pytest.fixture(autouse=True)
def clear_global_state():
    request_windows.clear()
    app.dependency_overrides.clear()
    yield
    request_windows.clear()
    app.dependency_overrides.clear()


@pytest.fixture
def isolated_client(tmp_path: Path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'quality.sqlite3'}",
        connect_args={"check_same_thread": False},
    )
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)

    def override_db():
        with TestingSession() as db:
            yield db

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as client:
        yield client, TestingSession


def test_chat_normalizes_question_and_rejects_invalid_topics(isolated_client):
    client, _ = isolated_client
    valid = client.post("/api/chat", json={"question": "   manure records?   "})
    assert valid.status_code == 200
    assert client.post("/api/chat", json={"question": "   "}).status_code == 422
    assert (
        client.post(
            "/api/chat", json={"question": "manure records?", "topics": ["../../admin"]}
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/chat", json={"question": "manure records?", "unexpected": True}
        ).status_code
        == 422
    )


def test_input_boundaries_cover_lengths_and_farm_numbers(isolated_client):
    client, _ = isolated_client
    assert client.post("/api/chat", json={"question": "x" * 2000}).status_code == 200
    assert client.post("/api/chat", json={"question": "x" * 2001}).status_code == 422
    assert client.post(
        "/api/chat",
        json={"question": "permit question", "farm_context": {"animal_unit_capacity": 0}},
    ).status_code == 422
    assert client.post(
        "/api/chat",
        json={"question": "permit question", "farm_context": {"county": "N" * 101}},
    ).status_code == 422


def test_api_contract_rejects_malformed_json_and_unsupported_method(isolated_client):
    client, _ = isolated_client
    malformed = client.post(
        "/api/chat",
        content=b'{"question":',
        headers={"Content-Type": "application/json"},
    )
    assert malformed.status_code == 422
    assert malformed.headers["content-type"].startswith("application/json")
    assert (
        client.put("/api/chat", json={"question": "valid question"}).status_code == 405
    )
    assert client.get("/does-not-exist").status_code == 404


def test_request_size_limit_and_security_headers_apply_to_rejections(isolated_client):
    client, _ = isolated_client
    response = client.post(
        "/api/chat",
        content=b"x" * (MAX_REQUEST_BODY_BYTES + 1),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 413
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
    assert response.headers["cache-control"] == "no-store"


def test_rate_limit_cannot_be_bypassed_with_forwarded_for_header(isolated_client):
    client, _ = isolated_client
    request_windows["testclient"].extend([time.monotonic()] * 20)
    response = client.post(
        "/api/chat",
        json={"question": "valid compliance question"},
        headers={"X-Forwarded-For": "203.0.113.99"},
    )
    assert response.status_code == 429
    assert response.headers["x-content-type-options"] == "nosniff"


def test_cors_allows_configured_origin_and_rejects_hostile_origin(isolated_client):
    client, _ = isolated_client
    trusted = client.options(
        "/api/chat",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert trusted.status_code == 200
    assert trusted.headers["access-control-allow-origin"] == "http://localhost:3000"
    hostile = client.options(
        "/api/chat",
        headers={
            "Origin": "https://attacker.example",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert hostile.status_code == 400
    assert "access-control-allow-origin" not in hostile.headers


def test_conversation_history_requires_admin_authorization(
    isolated_client, monkeypatch
):
    client, Session = isolated_client
    monkeypatch.setattr("app.main.settings.admin_api_key", "test-admin-key")
    with Session() as db:
        conversation = Conversation()
        db.add(conversation)
        db.flush()
        db.add(
            Message(
                conversation_id=conversation.id,
                role="user",
                content={"question": "private farm question"},
            )
        )
        db.commit()
        conversation_id = conversation.id

    assert client.get(f"/api/conversations/{conversation_id}").status_code == 401
    assert (
        client.get(
            f"/api/conversations/{conversation_id}", headers={"X-Admin-Key": "wrong"}
        ).status_code
        == 401
    )
    authorized = client.get(
        f"/api/conversations/{conversation_id}",
        headers={"X-Admin-Key": "test-admin-key"},
    )
    assert authorized.status_code == 200
    assert (
        authorized.json()["messages"][0]["content"]["question"]
        == "private farm question"
    )


def test_admin_summary_rejects_missing_and_invalid_key(isolated_client, monkeypatch):
    client, _ = isolated_client
    monkeypatch.setattr("app.main.settings.admin_api_key", "test-admin-key")
    assert client.get("/api/admin/summary").status_code == 401
    assert (
        client.get("/api/admin/summary", headers={"X-Admin-Key": "wrong"}).status_code
        == 401
    )


def test_feedback_and_bookmarks_are_idempotent(isolated_client):
    client, Session = isolated_client
    first_feedback = client.post(
        "/api/feedback", json={"answer_id": "answer-1", "rating": "not_helpful"}
    )
    second_feedback = client.post(
        "/api/feedback",
        json={
            "answer_id": "answer-1",
            "rating": "not_helpful",
            "comment": "Missing permit threshold",
        },
    )
    first_bookmark = client.post("/api/bookmarks", json={"answer_id": "answer-1"})
    second_bookmark = client.post("/api/bookmarks", json={"answer_id": "answer-1"})
    assert first_feedback.json()["id"] == second_feedback.json()["id"]
    assert first_bookmark.json()["id"] == second_bookmark.json()["id"]
    with Session() as db:
        assert db.scalar(select(func.count(Feedback.id))) == 1
        assert db.scalar(select(Feedback.comment)) == "Missing permit threshold"
        assert db.scalar(select(func.count(Bookmark.id))) == 1


def test_no_cookie_session_is_created_for_public_api(isolated_client):
    client, _ = isolated_client
    response = client.get("/healthz")
    assert response.status_code == 200
    assert "set-cookie" not in response.headers


def test_production_readiness_rejects_an_empty_corpus(isolated_client, monkeypatch):
    client, _ = isolated_client
    monkeypatch.setattr("app.main.settings.environment", "production")
    monkeypatch.setattr("app.main.settings.openai_api_key", "configured-for-test")
    response = client.get("/healthz")
    assert response.status_code == 503
    assert response.json()["detail"] == "Authoritative corpus unavailable"


def test_open_redirect_payloads_do_not_change_fixed_destination(isolated_client):
    client, _ = isolated_client
    for suffix in (
        "?next=https://attacker.example",
        "?url=//attacker.example",
        "?redirect=https:%2F%2Fattacker.example",
    ):
        response = client.get(f"/{suffix}", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "https://wayan.com/copilot/"


def test_ssrf_allowlist_rejects_encoded_and_non_http_destinations():
    rejected = [
        "http://127.0.0.1/admin",
        "https://127.0.0.1/admin",
        "https://[::1]/admin",
        "https://169.254.169.254/latest/meta-data/",
        "file:///etc/passwd",
        "gopher://dwee.nebraska.gov/resource",
        "https://dwee.nebraska.gov@attacker.example/",
        "https://dwee.nebraska.gov.attacker.example/",
    ]
    assert all(not _allowed_url(url) for url in rejected)


def test_manual_source_reader_rejects_traversal_absolute_paths_and_symlinks(
    tmp_path, monkeypatch
):
    outside = tmp_path / "outside.pdf"
    outside.write_bytes(b"not a real PDF")
    root = tmp_path / "root"
    root.mkdir()
    link = root / "escape.pdf"
    link.symlink_to(outside)
    monkeypatch.setattr("app.ingest.MANUAL_SOURCE_ROOT", root)
    read_manual_source.cache_clear()
    with pytest.raises(ValueError):
        read_manual_source("../outside.pdf")
    with pytest.raises(ValueError):
        read_manual_source(str(outside))
    with pytest.raises(ValueError):
        read_manual_source("escape.pdf")


def test_xss_and_sql_payloads_are_treated_as_plain_data(isolated_client):
    client, Session = isolated_client
    payload = "<img src=x onerror=alert(1)> '; DROP TABLE conversations; --"
    response = client.post("/api/chat", json={"question": payload})
    assert response.status_code == 200
    assert response.json()["evidence_status"] == "insufficient"
    with Session() as db:
        assert db.scalar(select(func.count(Conversation.id))) == 1
