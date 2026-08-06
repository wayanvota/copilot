import math
import re
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from .config import settings
from .embeddings import embed_texts
from .models import Chunk, Document

TOKEN_RE = re.compile(r"[a-z0-9]+")


@dataclass
class RetrievedChunk:
    chunk: Chunk
    score: float


def _tokens(text: str) -> set[str]:
    return {token for token in TOKEN_RE.findall(text.lower()) if len(token) > 2}


def _expand_query(question: str) -> tuple[str, bool]:
    tokens = _tokens(question)
    acreage_intent = bool(tokens & {"land", "acre", "acres", "acreage"}) and bool(
        tokens & {"manure", "spread", "apply", "application", "pig", "pigs", "hog", "hogs", "swine"}
    )
    if not acreage_intent:
        return question, False
    return (
        question
        + " manure management plan annual manure produced planned application rate total acres "
        + "sufficient land base crop nitrogen phosphorus nutrient"
    ), True


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return dot / norm if norm else 0.0


def hybrid_search(db: Session, question: str, source_tiers: list[int], topics: list[str]) -> list[RetrievedChunk]:
    statement = (
        select(Chunk)
        .join(Chunk.document)
        .options(joinedload(Chunk.document))
        .where(Document.status == "active", Document.source_tier.in_(source_tiers))
    )
    if topics:
        statement = statement.where(Document.topic.in_(topics))
    candidates = db.scalars(statement.limit(1200)).all()
    if not candidates:
        return []

    expanded_question, acreage_intent = _expand_query(question)
    query_embedding = embed_texts([expanded_question])[0]
    question_tokens = _tokens(expanded_question)
    ranked: list[RetrievedChunk] = []
    for chunk in candidates:
        chunk_tokens = _tokens(chunk.content)
        keyword_score = len(question_tokens & chunk_tokens) / max(len(question_tokens), 1)
        semantic_score = max(_cosine(query_embedding, list(chunk.embedding)), 0.0)
        jurisdiction_bonus = 0.04 if chunk.document.jurisdiction == "Iowa" else 0.0
        tier_bonus = 0.03 if chunk.document.source_tier == 1 else 0.0
        intent_bonus = 0.14 if acreage_intent and "manure management plan" in chunk.document.title.lower() else 0.0
        score = semantic_score * 0.67 + keyword_score * 0.26 + jurisdiction_bonus + tier_bonus + intent_bonus
        ranked.append(RetrievedChunk(chunk=chunk, score=score))
    ranked.sort(key=lambda item: item.score, reverse=True)

    results: list[RetrievedChunk] = []
    per_document: dict[str, int] = {}
    for item in ranked:
        doc_id = item.chunk.document_id
        if per_document.get(doc_id, 0) >= 3:
            continue
        results.append(item)
        per_document[doc_id] = per_document.get(doc_id, 0) + 1
        if len(results) >= settings.retrieval_limit:
            break
    return results
