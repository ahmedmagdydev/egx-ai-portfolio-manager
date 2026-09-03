from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..config import Settings, get_settings
from ..db_session import get_session
from ..repositories.documents import create_document, get_documents
from ..services.rag import search_documents

router = APIRouter(prefix="/api/documents", tags=["documents"])


class DocumentCreate(BaseModel):
    symbol: str | None = None
    document_type: str
    title: str
    language: str = "en"
    content: str
    source: str
    source_url: str | None = None
    published_at: datetime | None = None


class DocumentResponse(BaseModel):
    id: str
    symbol: str | None
    document_type: str
    title: str
    language: str
    source: str
    source_url: str | None
    checksum: str
    status: str
    version: int
    published_at: str | None
    chunk_count: int


class DocumentListItem(BaseModel):
    id: str
    symbol: str | None
    document_type: str
    title: str
    language: str
    source: str
    status: str
    published_at: str | None


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    symbol: str | None = None
    document_type: str | None = None
    language: str | None = None
    as_of: datetime | None = None
    top_k: int = Field(default=5, ge=1, le=50)


@router.post("", response_model=DocumentResponse, status_code=201)
def ingest_document(
    data: DocumentCreate,
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> DocumentResponse:
    if data.published_at is not None and data.published_at.tzinfo is None:
        data.published_at = data.published_at.replace(tzinfo=UTC)
    document = create_document(
        session,
        settings,
        symbol=data.symbol,
        document_type=data.document_type,
        title=data.title,
        language=data.language,
        content=data.content,
        source=data.source,
        source_url=data.source_url,
        published_at=data.published_at,
    )
    return DocumentResponse(
        id=str(document.id),
        symbol=document.symbol,
        document_type=document.document_type,
        title=document.title,
        language=document.language,
        source=document.source,
        source_url=document.source_url,
        checksum=document.checksum,
        status=document.status,
        version=document.version,
        published_at=document.published_at.isoformat() if document.published_at else None,
        chunk_count=len(document.chunks),
    )


@router.get("", response_model=list[DocumentListItem])
def list_documents(
    symbol: str | None = Query(default=None),
    document_type: str | None = Query(default=None),
    language: str | None = Query(default=None),
    as_of: datetime | None = Query(default=None),
    session: Session = Depends(get_session),
) -> list[DocumentListItem]:
    if as_of is not None and as_of.tzinfo is None:
        as_of = as_of.replace(tzinfo=UTC)
    documents = get_documents(
        session,
        symbol=symbol,
        document_type=document_type,
        language=language,
        as_of=as_of,
    )
    return [
        DocumentListItem(
            id=str(doc.id),
            symbol=doc.symbol,
            document_type=doc.document_type,
            title=doc.title,
            language=doc.language,
            source=doc.source,
            status=doc.status,
            published_at=doc.published_at.isoformat() if doc.published_at else None,
        )
        for doc in documents
    ]


@router.post("/search")
def search(
    request: SearchRequest,
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> dict:
    if request.as_of is not None and request.as_of.tzinfo is None:
        request.as_of = request.as_of.replace(tzinfo=UTC)
    results = search_documents(
        session,
        settings,
        query=request.query,
        symbol=request.symbol,
        document_type=request.document_type,
        language=request.language,
        as_of=request.as_of,
        top_k=request.top_k,
    )
    return {
        "query": request.query,
        "filters": {
            "symbol": request.symbol,
            "document_type": request.document_type,
            "language": request.language,
            "as_of": request.as_of.isoformat() if request.as_of else None,
        },
        "top_k": request.top_k,
        "results": results,
    }
