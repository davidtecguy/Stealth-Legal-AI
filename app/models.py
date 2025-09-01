from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from typing import Dict, List, Set
import hashlib
import json

Base = declarative_base()

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    etag = Column(String(64), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __init__(self, title: str, content: str):
        self.title = title
        self.content = content
        self.etag = self._generate_etag()
    
    def _generate_etag(self) -> str:
        """Generate ETag based on content hash."""
        content_hash = hashlib.md5(self.content.encode()).hexdigest()
        return f'"{content_hash}"'
    
    def update_content(self, new_content: str):
        """Update content and regenerate ETag."""
        self.content = new_content
        self.etag = self._generate_etag()

class SearchIndex:
    """In-memory inverted index for fast document search."""
    
    def __init__(self):
        self.index: Dict[str, Dict[int, List[int]]] = {}  # word -> {doc_id -> [positions]}
        self.documents: Dict[int, str] = {}
    
    def add_document(self, doc_id: int, content: str):
        """Add document to search index."""
        self.documents[doc_id] = content
        words = self._tokenize(content)
        
        for position, word in enumerate(words):
            if word not in self.index:
                self.index[word] = {}
            if doc_id not in self.index[word]:
                self.index[word][doc_id] = []
            self.index[word][doc_id].append(position)
    
    def remove_document(self, doc_id: int):
        """Remove document from search index."""
        if doc_id in self.documents:
            del self.documents[doc_id]
            # Remove from all word indices
            for word in self.index:
                if doc_id in self.index[word]:
                    del self.index[word][doc_id]
    
    def update_document(self, doc_id: int, content: str):
        """Update document in search index."""
        self.remove_document(doc_id)
        self.add_document(doc_id, content)
    
    def search(self, query: str, limit: int = 10, offset: int = 0) -> List[dict]:
        """Search for documents containing query terms."""
        query_words = self._tokenize(query.lower())
        if not query_words:
            return []
        
        # Find documents containing all query words
        doc_scores = {}
        
        for word in query_words:
            if word in self.index:
                for doc_id, positions in self.index[word].items():
                    if doc_id not in doc_scores:
                        doc_scores[doc_id] = {'score': 0, 'matches': []}
                    doc_scores[doc_id]['score'] += len(positions)
                    doc_scores[doc_id]['matches'].extend(positions)
        
        # Sort by score and get context
        results = []
        sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1]['score'], reverse=True)
        
        for doc_id, score_info in sorted_docs[offset:offset + limit]:
            context = self._get_context(doc_id, score_info['matches'])
            results.append({
                'document_id': doc_id,
                'title': f"Document {doc_id}",  # In real app, get from DB
                'score': score_info['score'],
                'context': context
            })
        
        return results
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization - split on whitespace and punctuation."""
        import re
        # Remove punctuation and split on whitespace
        words = re.findall(r'\b\w+\b', text.lower())
        # Filter out common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        return [word for word in words if word not in stop_words and len(word) > 2]
    
    def _get_context(self, doc_id: int, positions: List[int], context_size: int = 50) -> List[str]:
        """Get context around matched positions."""
        if doc_id not in self.documents:
            return []
        
        content = self.documents[doc_id]
        words = content.split()
        contexts = []
        
        for pos in positions[:5]:  # Limit to first 5 matches
            start = max(0, pos - context_size // 2)
            end = min(len(words), pos + context_size // 2)
            context_words = words[start:end]
            contexts.append(' '.join(context_words))
        
        return contexts
