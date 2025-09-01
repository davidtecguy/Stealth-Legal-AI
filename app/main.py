from fastapi import FastAPI, Depends, HTTPException, Query, Header, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import os

from app.database import get_db, engine
from app.models import Base, Document
from app.schemas import (
    DocumentCreate, DocumentResponse, DocumentChanges, SearchResponse,
    SemanticSearchResponse, LLMAnalysisResponse, DocumentImprovementResponse,
    DocumentImprovementRequest, DocumentClassification, LegalTerm, FileUploadResponse, DocumentMetadata
)
from app.services.document_service import DocumentService
from app.services.llm_service import LLMService
from app.services.search_service import search_service

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Stealth Legal AI API",
    description="Intelligent Document Management & Legal Analysis",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
document_service = DocumentService()
llm_service = LLMService()

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    # Initialize search index from existing documents
    db = next(get_db())
    try:
        indexed_count = search_service.reindex_all_documents(db)
        print(f"Initialized search index with {indexed_count} documents")
    finally:
        db.close()

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Stealth Legal AI API"}

@app.get("/llm/status")
async def get_llm_status():
    """Get LLM service status and configuration."""
    return llm_service.get_status()

@app.post("/documents/upload", response_model=FileUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    db: Session = Depends(get_db)
):
    """Upload a new document file."""
    try:
        # Validate file type
        supported_types = document_service.get_supported_file_types()
        file_extension = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
        
        if file_extension not in supported_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type. Only PDF and DOC files are allowed. Received: {file_extension}"
            )
        
        # Create document from file upload
        document = document_service.create_document(db, DocumentCreate(title=title, filename=file.filename, file_type=file_extension), file)
        
        return FileUploadResponse(
            filename=document.filename,
            file_path=document.file_path,
            file_type=document.file_type,
            file_size=document.file_size,
            message=f"Document '{title}' uploaded successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/documents", response_model=List[DocumentResponse])
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """List all documents with pagination."""
    return document_service.get_documents(db, skip, limit)

# Search endpoints (must come before document_id routes)
@app.get("/documents/search", response_model=SearchResponse)
async def search_documents(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Search across all documents."""
    try:
        results = document_service.search_documents(q, limit, offset)
        return SearchResponse(**results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/semantic-search", response_model=SemanticSearchResponse)
async def semantic_search_documents(
    q: str = Query(..., min_length=1, description="Semantic search query"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Perform semantic search across documents using LLM."""
    try:
        # Get all documents for semantic analysis
        documents = document_service.get_documents(db, offset, limit + 50)
        
        # Convert SQLAlchemy objects to dictionaries
        doc_dicts = [
            {
                "id": doc.id,
                "title": doc.title,
                "filename": doc.filename,
                "file_type": doc.file_type,
                "content": doc.content,
                "etag": doc.etag,
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
                "updated_at": doc.updated_at.isoformat() if doc.updated_at else None
            }
            for doc in documents
        ]
        
        # Perform semantic search
        results = llm_service.semantic_search(q, doc_dicts)
        
        # Limit results
        results = results[:limit]
        
        return SemanticSearchResponse(
            query=q,
            results=results,
            total_results=len(results),
            search_method="llm_semantic" if llm_service.enabled else "keyword_fallback",
            llm_enabled=llm_service.enabled
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific document by ID."""
    document = document_service.get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document

@app.get("/documents/{document_id}/metadata", response_model=DocumentMetadata)
async def get_document_metadata(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed metadata for a document."""
    metadata = document_service.get_document_metadata(db, document_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="Document not found")
    return metadata

@app.get("/documents/{document_id}/download")
async def download_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Download a document file."""
    document = document_service.get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if not os.path.exists(document.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    # Return file for download
    from fastapi.responses import FileResponse
    return FileResponse(
        path=document.file_path,
        filename=document.filename,
        media_type=document_service.get_supported_file_types().get(document.file_type, 'application/octet-stream')
    )

@app.patch("/documents/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: int,
    changes: DocumentChanges,
    if_match: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Apply changes to a document with concurrency control."""
    try:
        if not if_match:
            raise HTTPException(status_code=428, detail="If-Match header required for concurrency control")
        
        document = document_service.update_document(db, document_id, changes, if_match)
        return document
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/documents/{document_id}")
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Delete a document and its associated file."""
    success = document_service.delete_document(db, document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": "Document deleted successfully"}

# LLM Analysis Endpoints
@app.post("/documents/{document_id}/analyze", response_model=LLMAnalysisResponse)
async def analyze_document_llm(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Analyze document using LLM for legal insights."""
    try:
        document = document_service.get_document(db, document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        if not document.content:
            raise HTTPException(status_code=400, detail="Document has no extractable content")
        
        analysis = llm_service.analyze_document(document.content)
        return analysis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/documents/{document_id}/improve", response_model=DocumentImprovementResponse)
async def improve_document_llm(
    document_id: int,
    improvement_request: DocumentImprovementRequest,
    db: Session = Depends(get_db)
):
    """Get LLM-powered document improvement suggestions."""
    try:
        document = document_service.get_document(db, document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        if not document.content:
            raise HTTPException(status_code=400, detail="Document has no extractable content")
        
        improvement = llm_service.improve_document(
            document.content,
            improvement_request.improvement_type,
            improvement_request.specific_focus
        )
        return improvement
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/{document_id}/classify", response_model=DocumentClassification)
async def classify_document_llm(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Classify document type using LLM."""
    try:
        document = document_service.get_document(db, document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        if not document.content:
            raise HTTPException(status_code=400, detail="Document has no extractable content")
        
        classification = llm_service.classify_document(document.content)
        return classification
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/{document_id}/extract-terms", response_model=List[LegalTerm])
async def extract_legal_terms_llm(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Extract legal terms from document using LLM."""
    try:
        document = document_service.get_document(db, document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        if not document.content:
            raise HTTPException(status_code=400, detail="Document has no extractable content")
        
        terms = llm_service.extract_legal_terms(document.content)
        return terms
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/file-types")
async def get_supported_file_types():
    """Get list of supported file types for upload."""
    return document_service.get_supported_file_types()

@app.get("/documents/stats")
async def get_document_stats(db: Session = Depends(get_db)):
    """Get document statistics and system information."""
    return document_service.get_document_stats(db)

@app.post("/documents/reindex")
async def reindex_documents(db: Session = Depends(get_db)):
    """Manually reindex all documents for search."""
    try:
        indexed_count = search_service.reindex_all_documents(db)
        return {
            "message": f"Successfully reindexed {indexed_count} documents",
            "indexed_documents": indexed_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/search-status")
async def get_search_status():
    """Get search index status for debugging."""
    return search_service.get_status()
