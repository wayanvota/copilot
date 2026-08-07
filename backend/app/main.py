import time
from collections import defaultdict, deque
from threading import Thread
from datetime import datetime, timedelta, timezone

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session, selectinload

from .config import settings
from .copilot import answer_question
from .database import SessionLocal, get_db
from .ingest import run as run_ingestion
from .models import Bookmark, Chunk, Conversation, Document, Feedback, Message, QueryLog
from .source_registry import APPROVED_SOURCES
from .schemas import (
    BookmarkRequest, ChatRequest, ChatResponse, ConversationMessageResponse, ConversationResponse,
    FeedbackRequest, SavedResponse, SourceResponse, SourceUpdateResponse,
)

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Evidence-constrained compliance decision support for Nebraska pork producers.",
    docs_url="/api/docs" if settings.environment != "production" else None,
    redoc_url=None,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-Admin-Key"],
)

request_windows: dict[str, deque[float]] = defaultdict(deque)


def _production_corpus_needs_sync() -> bool:
    """Return true only when production differs from the approved source registry."""
    if settings.environment != "production":
        return False
    approved_urls = {source["url"] for source in APPROVED_SOURCES}
    with SessionLocal() as db:
        stored_urls = set(db.scalars(select(Document.url)).all())
    return stored_urls != approved_urls


def _sync_production_corpus() -> None:
    try:
        run_ingestion(sync=True)
    except BaseException as exc:
        # Keep the API available and retain the prior corpus if a source or
        # embedding provider is temporarily unavailable. A later restart retries.
        print(f"Production corpus synchronization failed: {type(exc).__name__}: {exc}")


@app.on_event("startup")
def synchronize_approved_corpus() -> None:
    if _production_corpus_needs_sync():
        Thread(target=_sync_production_corpus, name="corpus-sync", daemon=True).start()


@app.middleware("http")
async def security_and_rate_limit(request: Request, call_next):
    if request.url.path == "/api/chat":
        key = request.client.host if request.client else "unknown"
        now = time.monotonic()
        window = request_windows[key]
        while window and window[0] < now - 60:
            window.popleft()
        if len(window) >= 20:
            return JSONResponse(status_code=429, content={"detail": "Too many questions. Try again in one minute."})
        window.append(now)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Cache-Control"] = "no-store" if request.url.path.startswith("/api/") else "no-cache"
    return response


def require_admin(x_admin_key: str | None = Header(default=None)) -> None:
    if not settings.admin_api_key or x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin key")


@app.exception_handler(Exception)
async def unhandled_error(_: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": "The service could not complete this request safely."})


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="https://wayan.com/copilot/", status_code=307)


@app.get("/healthz")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        document_count = db.scalar(select(func.count(Document.id))) or 0
        return {"status": "ok", "database": "ok", "jurisdiction": "Nebraska", "corpus_documents": document_count, "model": settings.openai_chat_model}
    except Exception:
        raise HTTPException(status_code=503, detail="Database unavailable")


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    if len(request.question) > settings.max_question_chars:
        raise HTTPException(status_code=422, detail=f"Question must be under {settings.max_question_chars} characters.")
    try:
        return answer_question(db, request)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@app.get("/api/sources", response_model=list[SourceResponse])
def sources(db: Session = Depends(get_db)):
    documents = db.scalars(select(Document).where(Document.status == "active").order_by(Document.source_tier, Document.agency, Document.title)).all()
    return [
        SourceResponse(
            id=doc.id, title=doc.title, agency=doc.agency, url=doc.url, topic=doc.topic,
            source_tier=doc.source_tier, jurisdiction=doc.jurisdiction, status=doc.status,
            publication_date=doc.publication_date.isoformat() if doc.publication_date else None,
            effective_date=doc.effective_date.isoformat() if doc.effective_date else None,
            retrieved_at=doc.retrieved_at,
        ) for doc in documents
    ]


@app.get("/api/updates", response_model=list[SourceUpdateResponse])
def source_updates(db: Session = Depends(get_db)):
    """Return only sources with more than one stored version. No change is implied otherwise."""
    documents = db.scalars(
        select(Document)
        .options(selectinload(Document.versions))
        .where(Document.status == "active")
        .order_by(Document.updated_at.desc())
    ).all()
    updates: list[SourceUpdateResponse] = []
    for document in documents:
        versions = sorted(document.versions, key=lambda version: version.retrieved_at, reverse=True)
        if len(versions) < 2:
            continue
        updates.append(SourceUpdateResponse(
            document_id=document.id, title=document.title, agency=document.agency, url=document.url,
            version_count=len(versions), latest_retrieved_at=versions[0].retrieved_at,
            previous_retrieved_at=versions[1].retrieved_at,
        ))
    return updates[:25]


@app.post("/api/feedback", response_model=SavedResponse, status_code=201)
def feedback(request: FeedbackRequest, db: Session = Depends(get_db)):
    record = Feedback(answer_id=request.answer_id, rating=request.rating, comment=request.comment)
    db.add(record)
    db.commit()
    return SavedResponse(id=record.id)


@app.post("/api/bookmarks", response_model=SavedResponse, status_code=201)
def bookmarks(request: BookmarkRequest, db: Session = Depends(get_db)):
    record = Bookmark(answer_id=request.answer_id)
    db.add(record)
    db.commit()
    return SavedResponse(id=record.id)


@app.get("/api/conversations/{conversation_id}", response_model=ConversationResponse)
def conversation(conversation_id: str, db: Session = Depends(get_db)):
    record = db.get(Conversation, conversation_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    messages = db.scalars(select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at)).all()
    return ConversationResponse(id=conversation_id, messages=[ConversationMessageResponse(role=item.role, content=item.content, created_at=item.created_at) for item in messages])


@app.get("/api/admin/summary", dependencies=[Depends(require_admin)])
def admin_summary(db: Session = Depends(get_db)):
    since = datetime.now(timezone.utc) - timedelta(days=7)
    unresolved = db.execute(
        select(QueryLog.question, func.count(QueryLog.id).label("count"))
        .where(QueryLog.created_at >= since, QueryLog.evidence_status == "insufficient")
        .group_by(QueryLog.question).order_by(func.count(QueryLog.id).desc()).limit(10)
    ).all()
    return {
        "corpus": {
            "documents": db.scalar(select(func.count(Document.id))) or 0,
            "chunks": db.scalar(select(func.count(Chunk.id))) or 0,
            "outdated_documents": db.scalar(select(func.count(Document.id)).where(Document.retrieved_at < datetime.now(timezone.utc) - timedelta(days=45))) or 0,
        },
        "last_7_days": {
            "questions": db.scalar(select(func.count(QueryLog.id)).where(QueryLog.created_at >= since)) or 0,
            "failed_questions": db.scalar(select(func.count(QueryLog.id)).where(QueryLog.created_at >= since, QueryLog.error_code.is_not(None))) or 0,
            "insufficient_answers": db.scalar(select(func.count(QueryLog.id)).where(QueryLog.created_at >= since, QueryLog.evidence_status == "insufficient")) or 0,
            "helpful": db.scalar(select(func.count(Feedback.id)).where(Feedback.created_at >= since, Feedback.rating == "helpful")) or 0,
            "not_helpful": db.scalar(select(func.count(Feedback.id)).where(Feedback.created_at >= since, Feedback.rating == "not_helpful")) or 0,
        },
        "top_evidence_gaps": [{"question": question, "count": count} for question, count in unresolved],
    }
