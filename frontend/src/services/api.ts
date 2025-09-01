import { 
  Document, 
  DocumentCreate, 
  DocumentChanges, 
  SearchResponse,
  LLMAnalysisResponse,
  DocumentImprovementRequest,
  DocumentImprovementResponse,
  SemanticSearchResponse,
  DocumentClassification,
  LegalTerm,
  LLMStatus
} from '../types';

const API_BASE_URL = 'http://localhost:8000';

class ApiService {
  private baseUrl = API_BASE_URL;

  private async request<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Unknown error' }));
      throw new Error(error.error || `HTTP error! status: ${response.status}`);
    }

    if (response.status === 204) {
      return {} as T; // No content
    }

    return response.json();
  }

  // Document CRUD operations
  async createDocument(document: DocumentCreate): Promise<Document> {
    return this.request<Document>('/documents', {
      method: 'POST',
      body: JSON.stringify(document),
    });
  }

  async getDocuments(skip = 0, limit = 100): Promise<Document[]> {
    return this.request<Document[]>(`/documents?skip=${skip}&limit=${limit}`);
  }

  async getDocument(id: number): Promise<Document> {
    return this.request<Document>(`/documents/${id}`);
  }

  async updateDocument(id: number, changes: DocumentChanges, etag?: string): Promise<Document> {
    const headers: Record<string, string> = {};
    if (etag) {
      headers['If-Match'] = etag;
    }

    return this.request<Document>(`/documents/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(changes),
      headers,
    });
  }

  async deleteDocument(id: number): Promise<void> {
    return this.request<void>(`/documents/${id}`, {
      method: 'DELETE',
    });
  }

  // Search operations
  async searchDocuments(query: string, limit = 10, offset = 0): Promise<SearchResponse> {
    return this.request<SearchResponse>(
      `/documents/search?q=${encodeURIComponent(query)}&limit=${limit}&offset=${offset}`
    );
  }

  async searchDocument(id: number, query: string, limit = 10, offset = 0): Promise<SearchResponse> {
    return this.request<SearchResponse>(
      `/documents/${id}/search?q=${encodeURIComponent(query)}&limit=${limit}&offset=${offset}`
    );
  }

  // Health check
  async healthCheck(): Promise<{ status: string; service: string }> {
    return this.request<{ status: string; service: string }>('/health');
  }

  // LLM Legal AI Methods
  async analyzeDocumentLLM(documentId: number): Promise<LLMAnalysisResponse> {
    const response = await fetch(`${this.baseUrl}/documents/${documentId}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    
    if (!response.ok) {
      throw new Error(`LLM Analysis failed: ${response.statusText}`);
    }
    
    return response.json();
  }

  async improveDocumentLLM(documentId: number, improvementType: string, specificFocus?: string): Promise<DocumentImprovementResponse> {
    const request: DocumentImprovementRequest = {
      document_id: documentId,
      improvement_type: improvementType,
      specific_focus: specificFocus
    };

    const response = await fetch(`${this.baseUrl}/documents/${documentId}/improve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request)
    });
    
    if (!response.ok) {
      throw new Error(`Document improvement failed: ${response.statusText}`);
    }
    
    return response.json();
  }

  async semanticSearch(query: string, limit: number = 10, offset: number = 0): Promise<SemanticSearchResponse> {
    const response = await fetch(`${this.baseUrl}/documents/semantic-search?q=${encodeURIComponent(query)}&limit=${limit}&offset=${offset}`);
    
    if (!response.ok) {
      throw new Error(`Semantic search failed: ${response.statusText}`);
    }
    
    return response.json();
  }

  async classifyDocumentLLM(documentId: number): Promise<DocumentClassification> {
    const response = await fetch(`${this.baseUrl}/documents/${documentId}/classify`);
    
    if (!response.ok) {
      throw new Error(`Document classification failed: ${response.statusText}`);
    }
    
    return response.json();
  }

  async extractLegalTermsLLM(documentId: number): Promise<LegalTerm[]> {
    const response = await fetch(`${this.baseUrl}/documents/${documentId}/extract-terms`);
    
    if (!response.ok) {
      throw new Error(`Legal term extraction failed: ${response.statusText}`);
    }
    
    return response.json();
  }

  async getLLMStatus(): Promise<LLMStatus> {
    const response = await fetch(`${this.baseUrl}/llm/status`);
    
    if (!response.ok) {
      throw new Error(`LLM status check failed: ${response.statusText}`);
    }
    
    return response.json();
  }
}

export const apiService = new ApiService();
