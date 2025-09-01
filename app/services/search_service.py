"""
Centralized search service to manage the search index.
"""

from app.models import SearchIndex
from sqlalchemy.orm import Session
from app.models import Document
from typing import Dict, Any, List
import threading

class SearchService:
    """Singleton search service to manage the global search index."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(SearchService, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.search_index = SearchIndex()
            self._initialized = True
    
    def reindex_all_documents(self, db: Session):
        """Rebuild the search index from all documents in the database."""
        self.search_index.clear()
        documents = db.query(Document).all()
        
        indexed_count = 0
        for document in documents:
            if document.content:
                self.search_index.add_document(
                    document.id, 
                    document.title, 
                    document.content, 
                    document.file_type,
                    document.filename or ""
                )
                indexed_count += 1
        
        return indexed_count
    
    def add_document(self, doc_id: int, title: str, content: str, file_type: str, filename: str = ""):
        """Add a document to the search index."""
        if content:
            self.search_index.add_document(doc_id, title, content, file_type, filename)
    
    def remove_document(self, doc_id: int):
        """Remove a document from the search index."""
        self.search_index.remove_document(doc_id)
    
    def search(self, query: str, limit: int = 10, offset: int = 0) -> Dict[str, Any]:
        """Search documents using the search index."""
        results = self.search_index.search(query, limit, offset)
        
        return {
            'results': results,
            'total': len(results),
            'limit': limit,
            'offset': offset
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get search index status."""
        return {
            "indexed_documents": self.search_index.get_document_count(),
            "search_index_keys": len(self.search_index.index),
            "document_ids": list(self.search_index.documents.keys()),
            "search_index_id": getattr(self.search_index, 'instance_id', 'unknown')
        }

# Global search service instance
search_service = SearchService()
