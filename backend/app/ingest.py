import argparse
import hashlib
import io
import re
from datetime import date, datetime, timezone
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from pypdf import PdfReader
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from .database import SessionLocal
from .embeddings import embed_texts
from .models import Chunk, Document, DocumentVersion
from .source_registry import ALLOWED_HOST_SUFFIXES, APPROVED_SOURCES

MANUAL_SOURCE_ROOT = Path(__file__).resolve().parents[1]


def _allowed_url(url: str) -> bool:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    return parsed.scheme == "https" and any(
        host == suffix or host.endswith(f".{suffix}")
        for suffix in ALLOWED_HOST_SUFFIXES
    )


def _clean_text(text: str) -> str:
    text = re.sub(r"\r", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Repair table-cell spacing in the official Nebraska reportable-disease PDF.
    text = re.sub(
        r"Porcine R\s*eproductive and\s+X?\s*Respiratory S\s*yndr\s*om\s*e\s*\(\s*PR\s*R\s*S\s*\)",
        "Porcine Reproductive and Respiratory Syndrome (PRRS)",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"Porcin\s*e\s+R\s*epr\s*odu\s*cti\s*ve\s+and\s+X?\s*"
        r"Respirator\s*y\s+S\s*yn\s*d\s*r\s*om\s*e\s*"
        r"\(\s*P\s*R\s*R\s*S\s*\)",
        "Porcine Reproductive and Respiratory Syndrome (PRRS)",
        text,
        flags=re.IGNORECASE,
    )
    return text.strip()


def fetch_source(url: str) -> str:
    if not _allowed_url(url):
        raise ValueError(f"Source host is not approved: {url}")
    with httpx.Client(
        follow_redirects=True,
        timeout=35.0,
        headers={"User-Agent": "NebraskaPorkComplianceCopilot/0.1 source-indexer"},
    ) as client:
        response = client.get(url)
        response.raise_for_status()
        if not _allowed_url(str(response.url)):
            raise ValueError("Source redirected to an unapproved host")
        content_type = response.headers.get("content-type", "").lower()
        if "pdf" in content_type or str(response.url).lower().endswith(".pdf"):
            reader = PdfReader(io.BytesIO(response.content))
            return _clean_text(
                "\n\n".join(
                    page.extract_text(extraction_mode="layout") or ""
                    for page in reader.pages
                )
            )
        soup = BeautifulSoup(response.text, "html.parser")
        for node in soup(
            ["script", "style", "nav", "footer", "header", "form", "noscript"]
        ):
            node.decompose()
        main = soup.find("main") or soup.find("article") or soup.body or soup
        return _clean_text(main.get_text("\n", strip=True))


@lru_cache(maxsize=64)
def read_manual_source(relative_path: str) -> str:
    path = (MANUAL_SOURCE_ROOT / relative_path).resolve()
    if MANUAL_SOURCE_ROOT not in path.parents:
        raise ValueError("Manual source path must stay inside the backend directory")
    if path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF manual sources are supported")
    reader = PdfReader(path)
    return _clean_text(
        "\n\n".join(
            page.extract_text(extraction_mode="layout") or "" for page in reader.pages
        )
    )


def chunk_text(text: str, size: int = 2400, overlap: int = 300) -> list[str]:
    paragraphs = [part.strip() for part in text.split("\n\n") if part.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if len(current) + len(paragraph) + 2 <= size:
            current = f"{current}\n\n{paragraph}".strip()
            continue
        if current:
            chunks.append(current)
        current = (
            f"{current[-overlap:]}\n\n{paragraph}".strip() if current else paragraph
        )
        while len(current) > size:
            chunks.append(current[:size])
            current = current[size - overlap :]
    if current:
        chunks.append(current)
    return chunks


def _parse_date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def ingest_source(db: Session, source: dict) -> str:
    try:
        if source.get("manual_path"):
            content = read_manual_source(source["manual_path"])
        else:
            content = fetch_source(source["url"])
        if len(content) < 200:
            raise ValueError("Fetched source did not contain enough readable text")
    except (httpx.HTTPError, ValueError, OSError) as exc:
        content = source["fallback_excerpt"]
        print(
            f"Using curated fallback excerpt for {source['title']}: {type(exc).__name__}"
        )

    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    document = db.scalar(select(Document).where(Document.url == source["url"]))
    previous_urls = source.get("previous_urls", [])
    previous_documents = (
        list(db.scalars(select(Document).where(Document.url.in_(previous_urls))))
        if previous_urls
        else []
    )
    if document is None and previous_documents:
        document = previous_documents.pop(0)
        document.url = source["url"]
    for previous_document in previous_documents:
        db.delete(previous_document)
    if previous_documents:
        db.flush()
    if document and document.content_hash == content_hash:
        return "unchanged"

    now = datetime.now(timezone.utc)
    if document is None:
        document = Document(
            title=source["title"],
            agency=source["agency"],
            url=source["url"],
            jurisdiction=source["jurisdiction"],
            topic=source["topic"],
            source_tier=source["source_tier"],
            document_type=source["document_type"],
            publication_date=_parse_date(source.get("publication_date")),
            effective_date=_parse_date(source.get("effective_date")),
            content_hash=content_hash,
            retrieved_at=now,
            status="active",
        )
        db.add(document)
        db.flush()
    else:
        document.title = source["title"]
        document.agency = source["agency"]
        document.jurisdiction = source["jurisdiction"]
        document.topic = source["topic"]
        document.source_tier = source["source_tier"]
        document.document_type = source["document_type"]
        document.publication_date = _parse_date(source.get("publication_date"))
        document.effective_date = _parse_date(source.get("effective_date"))
        document.content_hash = content_hash
        document.retrieved_at = now
        db.execute(delete(Chunk).where(Chunk.document_id == document.id))
        db.flush()

    db.add(
        DocumentVersion(
            document_id=document.id,
            content_hash=content_hash,
            content=content,
            retrieved_at=now,
        )
    )
    pieces = chunk_text(content)
    vectors: list[list[float]] = []
    for start in range(0, len(pieces), 64):
        vectors.extend(embed_texts(pieces[start : start + 64]))
    for ordinal, (piece, vector) in enumerate(zip(pieces, vectors)):
        db.add(
            Chunk(
                document_id=document.id,
                ordinal=ordinal,
                content=piece,
                token_count=max(1, len(piece) // 4),
                embedding=vector,
            )
        )
    return "created" if len(document.versions) == 0 else "updated"


def sync_registry(db: Session) -> int:
    """Remove documents that are no longer in the approved Nebraska corpus."""
    approved_urls = {source["url"] for source in APPROVED_SOURCES}
    removed = 0
    for document in db.scalars(
        select(Document).where(Document.url.not_in(approved_urls))
    ).all():
        db.delete(document)
        removed += 1
    db.commit()
    return removed


def run(seed_if_empty: bool = False, sync: bool = False) -> None:
    with SessionLocal() as db:
        if seed_if_empty and (db.scalar(select(func.count(Document.id))) or 0) > 0:
            print("Corpus already contains documents; skipping seed.")
            return
        results = {"created": 0, "updated": 0, "unchanged": 0, "failed": 0}
        for source in APPROVED_SOURCES:
            try:
                status = ingest_source(db, source)
                db.commit()
                results[status] += 1
            except Exception as exc:
                db.rollback()
                results["failed"] += 1
                print(
                    f"Failed to ingest {source['title']}: {type(exc).__name__}: {exc}"
                )
        if sync and not results["failed"]:
            results["removed"] = sync_registry(db)
        print(f"Ingestion complete: {results}")
        if results["failed"]:
            raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", action="store_true")
    parser.add_argument("--seed-if-empty", action="store_true")
    parser.add_argument(
        "--sync",
        action="store_true",
        help="Remove documents outside the approved Nebraska registry after a successful ingestion",
    )
    args = parser.parse_args()
    run(seed_if_empty=args.seed_if_empty, sync=args.sync)
