from sqlalchemy.orm import Session
from app.models import Document, SearchIndex
from app.schemas import DocumentCreate, ChangeOperation, ChangeTarget, ChangeRange
from typing import List, Optional, Tuple
import re

class DocumentService:
    def __init__(self):
        self.search_index = SearchIndex()
    
    def create_document(self, db: Session, document: DocumentCreate) -> Document:
        """Create a new document."""
        db_document = Document(title=document.title, content=document.content)
        db.add(db_document)
        db.commit()
        db.refresh(db_document)
        
        # Add to search index
        self.search_index.add_document(db_document.id, db_document.content)
        
        return db_document
    
    def get_document(self, db: Session, document_id: int) -> Optional[Document]:
        """Get document by ID."""
        return db.query(Document).filter(Document.id == document_id).first()
    
    def get_documents(self, db: Session, skip: int = 0, limit: int = 100) -> List[Document]:
        """Get all documents with pagination."""
        return db.query(Document).offset(skip).limit(limit).all()
    
    def delete_document(self, db: Session, document_id: int) -> bool:
        """Delete document by ID."""
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            db.delete(document)
            db.commit()
            # Remove from search index
            self.search_index.remove_document(document_id)
            return True
        return False
    
    def apply_changes(self, db: Session, document_id: int, changes: List[ChangeOperation], etag: Optional[str] = None) -> Tuple[Document, bool]:
        """
        Apply changes to document with concurrency control.
        Returns (document, has_changes)
        """
        document = self.get_document(db, document_id)
        if not document:
            raise ValueError("Document not found")
        
        # Check ETag for concurrency control
        if etag and document.etag != etag:
            raise ValueError("Document has been modified by another user")
        
        original_content = document.content
        new_content = original_content
        
        for change in changes:
            if change.operation == "replace":
                new_content = self._apply_replace_operation(new_content, change)
            else:
                raise ValueError(f"Unsupported operation: {change.operation}")
        
        # Only update if content actually changed
        if new_content != original_content:
            document.update_content(new_content)
            db.commit()
            db.refresh(document)
            
            # Update search index
            self.search_index.update_document(document_id, new_content)
            
            return document, True
        
        return document, False
    
    def _apply_replace_operation(self, content: str, change: ChangeOperation) -> str:
        """Apply a replace operation to content."""
        if change.target:
            return self._replace_by_text(content, change.target, change.replacement)
        elif change.range:
            return self._replace_by_range(content, change.range, change.replacement)
        else:
            raise ValueError("Either target or range must be specified")
    
    def _replace_by_text(self, content: str, target: ChangeTarget, replacement: str) -> str:
        """Replace text by finding target text and replacing specified occurrence."""
        target_text = target.text
        occurrence = target.occurrence
        
        # Find all occurrences
        positions = []
        start = 0
        while True:
            pos = content.find(target_text, start)
            if pos == -1:
                break
            positions.append(pos)
            start = pos + 1
        
        if not positions:
            raise ValueError(f"Target text '{target_text}' not found in document")
        
        if occurrence > len(positions):
            raise ValueError(f"Occurrence {occurrence} not found. Only {len(positions)} occurrences exist.")
        
        # Replace the specified occurrence
        target_pos = positions[occurrence - 1]
        return content[:target_pos] + replacement + content[target_pos + len(target_text):]
    
    def _replace_by_range(self, content: str, range_obj: ChangeRange, replacement: str) -> str:
        """Replace text by character range."""
        if range_obj.start >= len(content):
            raise ValueError("Start position exceeds document length")
        
        if range_obj.end > len(content):
            raise ValueError("End position exceeds document length")
        
        if range_obj.start >= range_obj.end:
            raise ValueError("Start position must be less than end position")
        
        return content[:range_obj.start] + replacement + content[range_obj.end:]
    
    def search_documents(self, query: str, limit: int = 10, offset: int = 0) -> dict:
        """Search across all documents."""
        results = self.search_index.search(query, limit, offset)
        return {
            "results": results,
            "total": len(results),
            "limit": limit,
            "offset": offset
        }
    
    def search_document(self, db: Session, document_id: int, query: str, limit: int = 10, offset: int = 0) -> dict:
        """Search within a specific document."""
        document = self.get_document(db, document_id)
        if not document:
            raise ValueError("Document not found")
        
        # Create temporary search index for this document only
        temp_index = SearchIndex()
        temp_index.add_document(document_id, document.content)
        
        results = temp_index.search(query, limit, offset)
        return {
            "results": results,
            "total": len(results),
            "limit": limit,
            "offset": offset
        }
