import asyncio

from fastapi.testclient import TestClient

from app.database import get_db
from app.health import DAY_SECONDS, DatabaseMonitor
from app.main import app


def test_daily_monitor_waits_a_day_after_failure_and_recovers(monkeypatch):
    calls = []
    sleeps = []

    def check():
        calls.append(True)
        if len(calls) == 1:
            raise RuntimeError("private connection details")
        return {"database": "ok"}

    monitor = DatabaseMonitor(check)

    async def sleep(seconds):
        sleeps.append(seconds)
        if len(sleeps) == 1:
            assert monitor.snapshot()["ok"] is False
            assert "private" not in str(monitor.snapshot())
        else:
            raise asyncio.CancelledError

    monkeypatch.setattr("app.health.asyncio.sleep", sleep)

    async def run():
        try:
            await monitor.run()
        except asyncio.CancelledError:
            pass

    asyncio.run(run())
    assert len(calls) == 2
    assert sleeps == [DAY_SECONDS, DAY_SECONDS]
    assert DAY_SECONDS == 86400
    assert monitor.snapshot()["ok"] is True
    assert monitor.snapshot()["checkedAt"]


def test_frequent_liveness_and_cached_diagnostics_never_open_database(monkeypatch):
    calls = []

    def forbidden_database():
        calls.append(True)
        raise AssertionError("HTTP health probes must not open a database")

    monitor = DatabaseMonitor(forbidden_database)
    monkeypatch.setattr("app.main.database_monitor", monitor)
    app.dependency_overrides[get_db] = forbidden_database
    try:
        client = TestClient(app)
        for _ in range(10):
            assert client.get("/healthz").status_code == 200
            assert client.get("/healthz/database").status_code == 503
        assert calls == []
        monitor.result = {"ok": False, "checkedAt": "2026-09-28T00:00:00Z"}
        assert client.get("/healthz").status_code == 200
        assert client.get("/healthz/database").status_code == 503
        monitor.result = {"ok": True, "checkedAt": "2026-09-28T00:00:00Z"}
        assert client.get("/healthz/database").status_code == 200
        assert calls == []
    finally:
        app.dependency_overrides.clear()


def test_production_lifecycle_starts_and_stops_monitor(monkeypatch):
    from threading import Event

    started = Event()
    stopped = Event()

    class Monitor:
        async def run(self):
            started.set()
            try:
                await asyncio.Event().wait()
            finally:
                stopped.set()

    monkeypatch.setattr("app.main.settings.environment", "production")
    monkeypatch.setattr("app.main._production_corpus_needs_sync", lambda: False)
    monkeypatch.setattr("app.main.database_monitor", Monitor())
    with TestClient(app):
        assert started.wait(timeout=2)
    assert stopped.wait(timeout=2)
