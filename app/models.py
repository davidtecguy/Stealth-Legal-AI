from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import Session
import hashlib
import re
from typing import List, Dict, Any, Optional
import os

Base = declarative_base()

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    filename = Column(String(255), nullable=False)  # Original filename
    file_path = Column(String(500), nullable=False)  # Path to stored file
    file_type = Column(String(50), nullable=False)  # pdf, doc, docx, txt
    file_size = Column(Integer, nullable=False)  # File size in bytes
    content = Column(Text, nullable=True)  # Extracted text content (nullable for large files)
    content_hash = Column(String(64), nullable=True)  # Hash of content for change detection
    etag = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Index for search performance
    __table_args__ = (
        Index('idx_documents_content', 'content'),
        Index('idx_documents_file_type', 'file_type'),
        Index('idx_documents_created_at', 'created_at'),
    )

class SearchIndex:
    """In-memory inverted index for document search."""
    
    def __init__(self):
        import uuid
        self.instance_id = str(uuid.uuid4())[:8]
        self.index: Dict[str, Dict[int, List[int]]] = {}
        self.documents: Dict[int, Dict[str, Any]] = {}
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'
        }
        print(f"SearchIndex created with ID: {self.instance_id}")
    
    def add_document(self, doc_id: int, title: str, content: str, file_type: str, filename: str = ""):
        """Add a document to the search index."""
        self.documents[doc_id] = {
            'title': title,
            'content': content,
            'file_type': file_type,
            'filename': filename
        }
        
        # Tokenize and index content
        tokens = self._tokenize(content)
        for position, token in enumerate(tokens):
            if token not in self.index:
                self.index[token] = {}
            if doc_id not in self.index[token]:
                self.index[token][doc_id] = []
            self.index[token][doc_id].append(position)
    
    def remove_document(self, doc_id: int):
        """Remove a document from the search index."""
        if doc_id in self.documents:
            del self.documents[doc_id]
            
        # Remove from all token indexes
        for token in self.index:
            if doc_id in self.index[token]:
                del self.index[token][doc_id]
    
    def search(self, query: str, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """Simple search for documents containing the query word."""
        if not query.strip():
            return []
        
        query_lower = query.lower().strip()
        results = []
        
        # Search through all documents
        for doc_id, doc in self.documents.items():
            content_lower = doc['content'].lower()
            
            # Check if query word exists in content
            if query_lower in content_lower:
                # Find all positions of the word
                positions = []
                start = 0
                while True:
                    pos = content_lower.find(query_lower, start)
                    if pos == -1:
                        break
                    positions.append(pos)
                    start = pos + 1
                
                # Get context snippets around matches
                context = self._get_simple_context(doc['content'], positions, query_lower)
                
                results.append({
                    'id': doc_id,
                    'title': doc['title'],
                    'filename': doc.get('filename', ''),
                    'file_type': doc['file_type'],
                    'relevance_score': len(positions),  # Simple score based on number of matches
                    'context': context
                })
        
        # Sort by number of matches (relevance score)
        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        # Apply pagination
        return results[offset:offset + limit]
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into searchable terms."""
        # Convert to lowercase and split on non-alphanumeric characters
        tokens = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        # Remove stop words and short tokens
        return [token for token in tokens if token not in self.stop_words and len(token) > 2]
    
    def _get_simple_context(self, content: str, positions: List[int], query: str, context_size: int = 100) -> List[str]:
        """Get simple context snippets around matched positions."""
        if not positions:
            return []
        
        context_snippets = []
        for pos in positions[:5]:  # Show up to 5 matches
            start = max(0, pos - context_size)
            end = min(len(content), pos + context_size)
            snippet = content[start:end]
            
            # Clean up snippet boundaries
            if start > 0:
                snippet = "..." + snippet
            if end < len(content):
                snippet = snippet + "..."
            
            context_snippets.append(snippet)
        
        return context_snippets
    
    def get_document_count(self) -> int:
        """Get total number of indexed documents."""
        return len(self.documents)
    
    def clear(self):
        """Clear all indexed documents."""
        self.index.clear()
        self.documents.clear()
