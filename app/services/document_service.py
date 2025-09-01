from sqlalchemy.orm import Session
from app.models import Document, SearchIndex
from app.schemas import DocumentCreate, DocumentChanges, ChangeOperation
from app.services.file_processor import FileProcessor
import hashlib
import os
from typing import List, Optional, Dict, Any
from datetime import datetime

class DocumentService:
    def __init__(self):
        self.search_index = SearchIndex()
        self.file_processor = FileProcessor()
    
    def create_document(self, db: Session, document_data: DocumentCreate, file) -> Document:
        """Create a new document from file upload."""
        # Process the uploaded file
        file_info = self.file_processor.process_upload(file, document_data.title)
        
        # Generate ETag from content hash
        etag = f'"{file_info["content_hash"]}"' if file_info["content_hash"] else f'"{hashlib.md5().hexdigest()}"'
        
        # Create document record
        document = Document(
            title=document_data.title,
            filename=file_info['filename'],
            file_path=file_info['file_path'],
            file_type=file_info['file_type'],
            file_size=file_info['file_size'],
            content=file_info['content'],
            content_hash=file_info['content_hash'],
            etag=etag
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # Add to search index if content is available
        if document.content:
            self.search_index.add_document(
                document.id, 
                document.title, 
                document.content, 
                document.file_type
            )
        
        return document
    
    def get_documents(self, db: Session, skip: int = 0, limit: int = 100) -> List[Document]:
        """Get documents with pagination."""
        return db.query(Document).offset(skip).limit(limit).all()
    
    def get_document(self, db: Session, document_id: int) -> Optional[Document]:
        """Get a specific document by ID."""
        return db.query(Document).filter(Document.id == document_id).first()
    
    def update_document(self, db: Session, document_id: int, changes: DocumentChanges, etag: str) -> Document:
        """Update document with changes."""
        document = self.get_document(db, document_id)
        if not document:
            raise ValueError("Document not found")
        
        # Verify ETag for concurrency control
        if document.etag != etag:
            raise ValueError("Document has been modified by another user")
        
        # Apply changes to content
        if document.content:
            updated_content = self._apply_changes(document.content, changes.changes)
            document.content = updated_content
            document.content_hash = hashlib.md5(updated_content.encode()).hexdigest()
            document.etag = f'"{document.content_hash}"'
            
            # Update search index
            self.search_index.remove_document(document.id)
            self.search_index.add_document(
                document.id, 
                document.title, 
                document.content, 
                document.file_type
            )
        
        db.commit()
        db.refresh(document)
        return document
    
    def delete_document(self, db: Session, document_id: int) -> bool:
        """Delete a document and its associated file."""
        document = self.get_document(db, document_id)
        if not document:
            return False
        
        # Remove from search index
        self.search_index.remove_document(document.id)
        
        # Delete file from storage
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
        
        # Delete database record
        db.delete(document)
        db.commit()
        
        return True
    
    def search_documents(self, query: str, limit: int = 10, offset: int = 0) -> Dict[str, Any]:
        """Search documents using the search index."""
        results = self.search_index.search(query, limit, offset)
        
        return {
            'results': results,
            'total': len(results),
            'limit': limit,
            'offset': offset
        }
    
    def get_document_metadata(self, db: Session, document_id: int) -> Optional[Dict[str, Any]]:
        """Get additional metadata for a document."""
        document = self.get_document(db, document_id)
        if not document:
            return None
        
        # Get file metadata
        file_metadata = self.file_processor.get_file_metadata(document.file_path)
        
        return {
            'id': document.id,
            'title': document.title,
            'filename': document.filename,
            'file_type': document.file_type,
            'file_size': document.file_size,
            'page_count': file_metadata.get('page_count'),
            'word_count': file_metadata.get('word_count'),
            'created_date': file_metadata.get('created_date'),
            'modified_date': file_metadata.get('modified_date'),
            'uploaded_at': document.created_at,
            'last_modified': document.updated_at
        }
    
    def get_supported_file_types(self) -> Dict[str, str]:
        """Get list of supported file types."""
        return self.file_processor.get_supported_types()
    
    def _apply_changes(self, content: str, changes: List[ChangeOperation]) -> str:
        """Apply changes to document content."""
        # Sort changes by position (for range-based changes)
        range_changes = [c for c in changes if c.range]
        text_changes = [c for c in changes if c.target]
        full_replacements = [c for c in changes if c.operation == 'replace' and not c.range and not c.target]
        
        # Apply full document replacements first
        for change in full_replacements:
            content = change.replacement
        
        # Apply range-based changes (they affect positions)
        for change in sorted(range_changes, key=lambda x: x.range.start, reverse=True):
            if change.range and change.range.start < change.range.end <= len(content):
                content = content[:change.range.start] + change.replacement + content[change.range.end:]
        
        # Apply text-based changes
        for change in text_changes:
            if change.target:
                content = self._replace_text_occurrence(
                    content, 
                    change.target.text, 
                    change.target.occurrence, 
                    change.replacement
                )
        
        return content
    
    def _replace_text_occurrence(self, content: str, target: str, occurrence: int, replacement: str) -> str:
        """Replace the nth occurrence of target text with replacement."""
        if occurrence < 1:
            return content
        
        start = 0
        for i in range(occurrence):
            pos = content.find(target, start)
            if pos == -1:
                break
            if i == occurrence - 1:
                return content[:pos] + replacement + content[pos + len(target):]
            start = pos + 1
        
        return content
    
    def reindex_documents(self, db: Session):
        """Rebuild the search index from all documents."""
        self.search_index.clear()
        documents = db.query(Document).all()
        
        for document in documents:
            if document.content:
                self.search_index.add_document(
                    document.id, 
                    document.title, 
                    document.content, 
                    document.file_type
                )
    
    def get_document_stats(self, db: Session) -> Dict[str, Any]:
        """Get document statistics."""
        total_docs = db.query(Document).count()
        total_size = db.query(Document).with_entities(
            db.func.sum(Document.file_size)
        ).scalar() or 0
        
        file_types = db.query(Document.file_type, db.func.count(Document.id)).group_by(
            Document.file_type
        ).all()
        
        return {
            'total_documents': total_docs,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'file_type_distribution': dict(file_types),
            'indexed_documents': self.search_index.get_document_count()
        }
