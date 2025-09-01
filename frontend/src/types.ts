// Basic Document Types
export interface Document {
  id: number;
  title: string;
  content: string;
  etag: string;
  created_at: string;
  updated_at: string;
}

export interface DocumentCreate {
  title: string;
  content: string;
}

export interface ChangeTarget {
  text: string;
  occurrence: number;
}

export interface ChangeRange {
  start: number;
  end: number;
}

export interface ChangeOperation {
  operation: string;
  target?: ChangeTarget;
  range?: ChangeRange;
  replacement: string;
}

export interface DocumentChanges {
  changes: ChangeOperation[];
}

export interface SearchResult {
  id: number;
  title: string;
  content: string;
  relevance_score: number;
  context: string[];
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  total_results: number;
  page: number;
  page_size: number;
}

export interface ErrorResponse {
  detail: string;
}

// LLM Legal AI Types
export interface LegalTerm {
  term: string;
  meaning: string;
  context: string;
  implications: string;
  source: string;
}

export interface LegalSuggestion {
  type: string;
  suggestion: string;
  example: string;
  source: string;
}

export interface DocumentAnalysis {
  key_terms: string[];
  risks: string[];
  document_type: string;
  summary: string;
  recommendations: string[];
  source: string;
}

export interface DocumentClassification {
  document_type: string;
  category: string;
  complexity: string;
  confidence: number;
  source: string;
}

export interface LLMAnalysisResponse {
  analysis: DocumentAnalysis;
  suggestions: LegalSuggestion[];
  terms: LegalTerm[];
  classification: DocumentClassification;
  llm_enabled: boolean;
  processing_time: number;
}

export interface SemanticSearchResult {
  id: number;
  title: string;
  content: string;
  relevance_score: number;
  search_method: string;
  llm_analysis?: string;
}

export interface SemanticSearchResponse {
  query: string;
  results: SemanticSearchResult[];
  total_results: number;
  search_method: string;
  llm_enabled: boolean;
}

export interface DocumentImprovementRequest {
  document_id: number;
  improvement_type: string;
  specific_focus?: string;
}

export interface DocumentImprovementResponse {
  document_id: number;
  improvements: LegalSuggestion[];
  original_content: string;
  suggested_changes: any[];
  llm_enabled: boolean;
}

export interface LLMStatus {
  enabled: boolean;
  model?: string;
  temperature: number;
  max_tokens: number;
  legal_terms_loaded: boolean;
  legal_phrases_loaded: boolean;
}
