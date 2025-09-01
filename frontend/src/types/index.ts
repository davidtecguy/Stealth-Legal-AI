export interface Document {
  id: number;
  title: string;
  content: string;
  etag: string;
  created_at: string;
  updated_at?: string;
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
  document_id: number;
  title: string;
  score: number;
  context: string[];
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
  limit: number;
  offset: number;
}

export interface ErrorResponse {
  error: string;
  code: number;
  details?: string;
}
