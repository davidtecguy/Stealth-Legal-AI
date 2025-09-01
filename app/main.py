from fastapi import FastAPI, Depends, HTTPException, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import time

from app.database import get_db, create_tables
from app.services import DocumentService
from app.services.llm_service import LLMService
from app.schemas import (
    DocumentBase, DocumentCreate, DocumentResponse, DocumentChanges,
    SearchResult, SearchResponse, ErrorResponse,
    LLMAnalysisResponse, SemanticSearchResponse, DocumentImprovementResponse,
    DocumentImprovementRequest, DocumentClassification, LegalTerm
)

# Create FastAPI app
app = FastAPI(
    title="Stealth Legal AI - Document Management Service",
    description="A full-stack document management service with redlining capabilities and search functionality",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize document service
document_service = DocumentService()

# Initialize LLM service
llm_service = LLMService()

# Initialize search index with existing documents
@app.on_event("startup")
async def initialize_search_index():
    """Initialize search index with existing documents."""
    from sqlalchemy.orm import Session
    db = next(get_db())
    try:
        documents = document_service.get_documents(db, 0, 1000)
        for doc in documents:
            document_service.search_index.add_document(doc.id, doc.content)
        print(f"Initialized search index with {len(documents)} documents")
    finally:
        db.close()

# Create tables on startup
@app.on_event("startup")
async def startup_event():
    create_tables()

# Error handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return ErrorResponse(
        error=str(exc),
        code=400,
        details="Invalid request data"
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return ErrorResponse(
        error="Internal server error",
        code=500,
        details=str(exc)
    )

# Document endpoints
@app.post("/documents", response_model=DocumentResponse, status_code=201)
async def create_document(
    document: DocumentCreate,
    db: Session = Depends(get_db)
):
    """Create a new document."""
    try:
        return document_service.create_document(db, document)
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
        documents = document_service.get_documents(db, offset, limit + 50)  # Get more for analysis
        
        # Convert SQLAlchemy objects to dictionaries
        doc_dicts = [
            {
                "id": doc.id,
                "title": doc.title,
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

@app.patch("/documents/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: int,
    changes: DocumentChanges,
    if_match: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Apply changes to a document with concurrency control."""
    try:
        document, has_changes = document_service.apply_changes(
            db, document_id, changes.changes, if_match
        )
        
        if not has_changes:
            return document  # No changes applied, return current document
            
        return document
    except ValueError as e:
        if "Document not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        elif "Document has been modified" in str(e):
            raise HTTPException(status_code=412, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))

@app.delete("/documents/{document_id}", status_code=204)
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Delete a document."""
    success = document_service.delete_document(db, document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")

@app.get("/documents/{document_id}/search", response_model=SearchResponse)
async def search_document(
    document_id: int,
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Search within a specific document."""
    try:
        results = document_service.search_document(db, document_id, q, limit, offset)
        return SearchResponse(**results)
    except ValueError as e:
        if "Document not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# LLM Legal AI Endpoints
@app.post("/documents/{document_id}/analyze", response_model=LLMAnalysisResponse)
async def analyze_document_llm(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Analyze document using LLM for legal insights."""
    try:
        # Get document
        document = document_service.get_document(db, document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        start_time = time.time()
        
        # Perform LLM analysis
        analysis = llm_service.analyze_document(document.content)
        suggestions = llm_service.suggest_improvements(document.content)
        terms = llm_service.extract_legal_terms(document.content)
        classification = llm_service.classify_document(document.content)
        
        processing_time = time.time() - start_time
        
        return LLMAnalysisResponse(
            analysis=analysis,
            suggestions=suggestions,
            terms=terms,
            classification=classification,
            llm_enabled=llm_service.enabled,
            processing_time=processing_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/documents/{document_id}/improve", response_model=DocumentImprovementResponse)
async def improve_document_llm(
    document_id: int,
    improvement_request: DocumentImprovementRequest,
    db: Session = Depends(get_db)
):
    """Get LLM-powered improvement suggestions for a document."""
    try:
        # Get document
        document = document_service.get_document(db, document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get improvements based on request type
        if improvement_request.improvement_type == "clarity":
            suggestions = llm_service.suggest_improvements(document.content)
        elif improvement_request.improvement_type == "legal_precision":
            suggestions = llm_service.suggest_improvements(document.content)
        elif improvement_request.improvement_type == "risk_mitigation":
            suggestions = llm_service.suggest_improvements(document.content)
        elif improvement_request.improvement_type == "consistency":
            suggestions = llm_service.suggest_improvements(document.content)
        else:
            suggestions = llm_service.suggest_improvements(document.content)
        
        # Create suggested changes
        suggested_changes = []
        for suggestion in suggestions:
            suggested_changes.append({
                "type": suggestion.type,
                "suggestion": suggestion.suggestion,
                "example": suggestion.example
            })
        
        return DocumentImprovementResponse(
            document_id=document_id,
            improvements=suggestions,
            original_content=document.content,
            suggested_changes=suggested_changes,
            llm_enabled=llm_service.enabled
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/documents/{document_id}/classify", response_model=DocumentClassification)
async def classify_document_llm(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Classify document type using LLM."""
    try:
        # Get document
        document = document_service.get_document(db, document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Perform classification
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
        # Get document
        document = document_service.get_document(db, document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Extract terms
        terms = llm_service.extract_legal_terms(document.content)
        
        return terms
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/llm/status")
async def get_llm_status():
    """Get LLM service status and configuration."""
    return {
        "enabled": llm_service.enabled,
        "model": llm_service.model if llm_service.enabled else None,
        "temperature": llm_service.temperature,
        "max_tokens": llm_service.max_tokens,
        "legal_terms_loaded": len(llm_service.legal_terms) > 0,
        "legal_phrases_loaded": len(llm_service.legal_phrases) > 0
    }

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Stealth Legal AI"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
