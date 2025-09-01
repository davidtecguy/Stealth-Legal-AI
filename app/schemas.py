from pydantic import BaseModel, Field
from typing import List, Optional, Union, Dict, Any
from datetime import datetime
import os

class DocumentBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    filename: str = Field(..., min_length=1, max_length=255)
    file_type: str = Field(..., description="File type (pdf, doc)")

class DocumentCreate(DocumentBase):
    pass

class DocumentResponse(DocumentBase):
    id: int
    file_path: str
    file_size: int
    content: Optional[str] = None
    content_hash: Optional[str] = None
    etag: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}

class FileUploadResponse(BaseModel):
    filename: str
    file_path: str
    file_type: str
    file_size: int
    message: str

class DocumentMetadata(BaseModel):
    title: str
    filename: str
    file_type: str
    file_size: int
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    created_date: Optional[datetime] = None
    modified_date: Optional[datetime] = None

class ChangeTarget(BaseModel):
    text: str = Field(..., description="Text to find and replace")
    occurrence: int = Field(1, ge=1, description="Which occurrence to replace (1-based)")

class ChangeRange(BaseModel):
    start: int = Field(..., ge=0, description="Start position (0-based)")
    end: int = Field(..., ge=0, description="End position (0-based)")

class ChangeOperation(BaseModel):
    operation: str = Field("replace", description="Operation type (currently only 'replace' supported)")
    target: Optional[ChangeTarget] = Field(None, description="Text-based targeting")
    range: Optional[ChangeRange] = Field(None, description="Position-based targeting")
    replacement: str = Field(..., description="New text to insert")

class DocumentChanges(BaseModel):
    changes: List[ChangeOperation] = Field(..., min_length=1, max_length=100)

class SearchResult(BaseModel):
    id: int
    title: str
    filename: str
    file_type: str
    relevance_score: float
    context: List[str]

class SearchResponse(BaseModel):
    results: List[SearchResult]
    total: int
    limit: int
    offset: int

class ErrorResponse(BaseModel):
    error: str
    code: int
    details: Optional[str] = None

# LLM Legal AI Schemas
class LegalTerm(BaseModel):
    term: str
    meaning: str
    context: str
    implications: str
    source: str

class LegalSuggestion(BaseModel):
    type: str
    suggestion: str
    example: str
    source: str

class DocumentAnalysis(BaseModel):
    key_terms: List[str]
    risks: List[str]
    document_type: str
    summary: str
    recommendations: List[str]
    source: str

class DocumentClassification(BaseModel):
    document_type: str
    category: str
    complexity: str
    confidence: float
    source: str

class LLMAnalysisResponse(BaseModel):
    analysis: DocumentAnalysis
    suggestions: List[LegalSuggestion]
    terms: List[LegalTerm]
    classification: DocumentClassification
    llm_enabled: bool
    processing_time: float

class SemanticSearchResult(BaseModel):
    id: int
    title: str
    filename: str
    file_type: str
    relevance_score: float
    search_method: str
    llm_analysis: Optional[str] = None

class SemanticSearchResponse(BaseModel):
    query: str
    results: List[SemanticSearchResult]
    total_results: int
    search_method: str
    llm_enabled: bool

class DocumentImprovementRequest(BaseModel):
    document_id: int
    improvement_type: str = Field(..., description="Type of improvement (clarity, legal_terms, structure)")
    specific_focus: Optional[str] = Field(None, description="Specific area to focus on")

class DocumentImprovementResponse(BaseModel):
    original_content: str
    improved_content: str
    changes_made: List[str]
    reasoning: str
    improvement_type: str

class LLMStatus(BaseModel):
    enabled: bool
    model: str
    temperature: float
    max_tokens: int
    legal_terms_count: int
    legal_phrases_count: int
