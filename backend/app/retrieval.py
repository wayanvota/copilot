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
    expansions: list[str] = []
    acreage_intent = bool(tokens & {"land", "acre", "acres", "acreage"}) and bool(
        tokens & {"manure", "spread", "apply", "application", "pig", "pigs", "hog", "hogs", "swine"}
    )
    if acreage_intent:
        expansions.append(
            "Nebraska nutrient management plan manure nutrient production land requirements "
            "planned application rate sufficient land crop nitrogen phosphorus soil tests"
        )
    if "prrs" in tokens:
        expansions.append(
            "Porcine reproductive and respiratory syndrome Nebraska reportable livestock disease "
            "Nebraska Department of Agriculture state veterinarian disease reporting list"
        )
    construction_intent = bool(
        tokens & {"construction", "barn", "confinement", "structure", "expansion"}
    ) and bool(
        tokens
        & {
            "separation",
            "distance",
            "distances",
            "neighbor",
            "neighbors",
            "well",
            "wells",
            "road",
            "roads",
            "sinkhole",
            "sinkholes",
        }
    )
    if construction_intent:
        expansions.append(
            "Nebraska Title 130 livestock waste control facility request for inspection Form A "
            "construction and operating permit Form B county conditional use separation distance "
            "residence well property line public use area"
        )
    permit_intent = bool(tokens & {"permit", "permits", "build", "building", "expand", "expansion", "construct", "construction"}) and bool(
        tokens & {"barn", "facility", "operation", "storage", "hog", "hogs", "pig", "pigs", "swine"}
    )
    if permit_intent:
        expansions.append(
            "Nebraska livestock waste control program Form A request for inspection animal feeding operation "
            "Form B construction operating permit county conditional use permit"
        )
    discharge_intent = bool(tokens & {"spill", "spilled", "discharge", "release", "overflow", "leak"}) and bool(
        tokens & {"manure", "waste", "lagoon", "pit", "stream", "water", "tile"}
    )
    if discharge_intent:
        expansions.append(
            "Nebraska notification discharge livestock waste verbal report within 24 hours written report within five days"
        )
    county_permit_intent = bool(tokens & {"county", "zoning", "conditional"}) and bool(
        tokens & {"permit", "permits", "barn", "facility", "operation", "hog", "hogs", "pig", "pigs", "swine"}
    )
    if county_permit_intent:
        expansions.append(
            "Nebraska Revised Statute county conditional use permit livestock facility zoning 54-2437 23-114.01"
        )
    if "h2a" in tokens:
        expansions.append(
            "H-2A temporary agricultural labor certification temporary or seasonal full-time agricultural work permanent year-round need"
        )
    foam_intent = bool(tokens & {"foam", "foaming"}) and bool(
        tokens & {"manure", "pit", "agitating", "agitation", "pumping"}
    )
    if foam_intent:
        expansions.append(
            "manure agitation pumping safety protocol evacuate extinguish ignition sources signage barriers "
            "ventilate methane hydrogen sulfide pump-out airflow"
        )
    agitation_safety_intent = bool(tokens & {"agitate", "agitating", "agitation", "pump", "pumping"}) and bool(
        tokens & {"manure", "pit", "lagoon", "storage"}
    )
    if agitation_safety_intent:
        expansions.append(
            "Nebraska manure agitation pumping safety adequately ventilate barns people animals hydrogen sulfide heavier than air"
        )
    if not expansions:
        return question, False
    return question + " " + " ".join(expansions), acreage_intent


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
    original_tokens = _tokens(question)
    question_tokens = _tokens(expanded_question)
    prrs_intent = "prrs" in original_tokens
    construction_distance_intent = bool(
        original_tokens & {"construction", "barn", "confinement", "structure", "expansion"}
    ) and bool(
        original_tokens
        & {"separation", "distance", "distances", "neighbor", "neighbors", "well", "wells", "road", "roads", "sinkhole", "sinkholes"}
    )
    foam_safety_intent = bool(original_tokens & {"foam", "foaming"}) and bool(
        original_tokens & {"manure", "pit", "agitating", "agitation", "pumping"}
    )
    agitation_safety_intent = bool(original_tokens & {"agitate", "agitating", "agitation", "pump", "pumping"}) and bool(
        original_tokens & {"manure", "pit", "lagoon", "storage"}
    )
    permit_intent = bool(original_tokens & {"permit", "permits", "build", "building", "expand", "expansion", "construct", "construction"}) and bool(
        original_tokens & {"barn", "facility", "operation", "storage", "hog", "hogs", "pig", "pigs", "swine"}
    )
    discharge_intent = bool(original_tokens & {"spill", "spilled", "discharge", "release", "overflow", "leak"}) and bool(
        original_tokens & {"manure", "waste", "lagoon", "pit", "stream", "water", "tile"}
    )
    county_permit_intent = bool(original_tokens & {"county", "zoning", "conditional"}) and bool(
        original_tokens & {"permit", "permits", "barn", "facility", "operation", "hog", "hogs", "pig", "pigs", "swine"}
    )
    h2a_intent = "h2a" in original_tokens
    ranked: list[RetrievedChunk] = []
    for chunk in candidates:
        chunk_tokens = _tokens(chunk.content)
        keyword_score = len(question_tokens & chunk_tokens) / max(len(question_tokens), 1)
        semantic_score = max(_cosine(query_embedding, list(chunk.embedding)), 0.0)
        jurisdiction_bonus = 0.04 if chunk.document.jurisdiction == "Nebraska" else 0.0
        tier_bonus = 0.03 if chunk.document.source_tier == 1 else 0.0
        title_lower = chunk.document.title.lower()
        intent_bonus = 0.0
        if acreage_intent and (
            "land requirements" in title_lower or "nutrient management plan" in title_lower
        ):
            intent_bonus += 0.2
        content_lower = chunk.content.lower()
        if prrs_intent and "porcine reproductive and respiratory syndrome" in content_lower:
            intent_bonus += 0.28
        if permit_intent and (
            "request for inspection" in content_lower or "construction and operating permit" in content_lower
        ):
            intent_bonus += 0.24
        if discharge_intent and "24 hours" in content_lower and ("five days" in content_lower or "5 days" in content_lower):
            intent_bonus += 0.28
        if county_permit_intent and (
            "county conditional use" in title_lower or "county livestock conditional uses" in title_lower
        ):
            intent_bonus += 0.32
        if h2a_intent and "h-2a" in title_lower:
            intent_bonus += 0.4
        if (
            construction_distance_intent
            and ("separation distance" in content_lower or "setback" in content_lower)
            and ("title 130" in title_lower or "siting" in title_lower)
        ):
            intent_bonus += 0.28
        if foam_safety_intent and "evacuate" in content_lower and "extinguish" in content_lower:
            intent_bonus += 0.2
        if agitation_safety_intent and "adequately ventilate" in content_lower and "hydrogen sulfide" in content_lower:
            intent_bonus += 0.32
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
