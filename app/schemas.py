from pydantic import BaseModel, Field
from typing import List, Optional, Union, Dict, Any
from datetime import datetime

class DocumentBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)

class DocumentCreate(DocumentBase):
    pass

class DocumentResponse(DocumentBase):
    id: int
    etag: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}

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
    document_id: int
    title: str
    score: int
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
    source: str = "rule_based"

class LegalSuggestion(BaseModel):
    type: str
    suggestion: str
    example: str
    source: str = "rule_based"

class DocumentAnalysis(BaseModel):
    key_terms: List[str]
    risks: List[str]
    document_type: str
    summary: str
    recommendations: List[str]
    source: str = "rule_based"

class DocumentClassification(BaseModel):
    document_type: str
    category: str
    complexity: str
    confidence: float
    source: str = "rule_based"

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
    content: str
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
    improvement_type: str = Field(..., description="Type of improvement: clarity, legal_precision, risk_mitigation, consistency")
    specific_focus: Optional[str] = Field(None, description="Specific area to focus on")

class DocumentImprovementResponse(BaseModel):
    document_id: int
    improvements: List[LegalSuggestion]
    original_content: str
    suggested_changes: List[Dict[str, Any]]
    llm_enabled: bool
