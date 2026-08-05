import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from .config import settings
from .copilot import answer_question
from .database import get_db
from .models import Bookmark, Chunk, Conversation, Document, Feedback, Message, QueryLog
from .schemas import (
    BookmarkRequest, ChatRequest, ChatResponse, ConversationMessageResponse, ConversationResponse,
    FeedbackRequest, SavedResponse, SourceResponse,
)

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Evidence-constrained compliance decision support for Iowa pork producers.",
    docs_url="/api/docs" if settings.environment != "production" else None,
    redoc_url=None,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Admin-Key"],
)

request_windows: dict[str, deque[float]] = defaultdict(deque)


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


def require_app_access(authorization: str | None = Header(default=None)) -> None:
    if not settings.app_access_token:
        return
    expected = f"Bearer {settings.app_access_token}"
    if authorization != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Valid producer access code required")


@app.exception_handler(Exception)
async def unhandled_error(_: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": "The service could not complete this request safely."})


@app.get("/healthz")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        document_count = db.scalar(select(func.count(Document.id))) or 0
        return {"status": "ok", "database": "ok", "corpus_documents": document_count, "model": settings.openai_chat_model}
    except Exception:
        raise HTTPException(status_code=503, detail="Database unavailable")


@app.post("/api/chat", response_model=ChatResponse, dependencies=[Depends(require_app_access)])
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


@app.post("/api/feedback", response_model=SavedResponse, status_code=201, dependencies=[Depends(require_app_access)])
def feedback(request: FeedbackRequest, db: Session = Depends(get_db)):
    record = Feedback(answer_id=request.answer_id, rating=request.rating, comment=request.comment)
    db.add(record)
    db.commit()
    return SavedResponse(id=record.id)


@app.post("/api/bookmarks", response_model=SavedResponse, status_code=201, dependencies=[Depends(require_app_access)])
def bookmarks(request: BookmarkRequest, db: Session = Depends(get_db)):
    record = Bookmark(answer_id=request.answer_id)
    db.add(record)
    db.commit()
    return SavedResponse(id=record.id)


@app.get("/api/conversations/{conversation_id}", response_model=ConversationResponse, dependencies=[Depends(require_app_access)])
def conversation(conversation_id: str, db: Session = Depends(get_db)):
    record = db.get(Conversation, conversation_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    messages = db.scalars(select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at)).all()
    return ConversationResponse(id=conversation_id, messages=[ConversationMessageResponse(role=item.role, content=item.content, created_at=item.created_at) for item in messages])


@app.get("/api/admin/summary", dependencies=[Depends(require_admin)])
def admin_summary(db: Session = Depends(get_db)):
    since = datetime.now(timezone.utc) - timedelta(days=7)
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
    }
