#!/usr/bin/env python3
"""
Database migration script to update existing database structure for file-based documents.
This script will:
1. Create new columns for file-based documents
2. Migrate existing text documents to file-based format
3. Update the search index
"""

import sqlite3
import os
import hashlib
from pathlib import Path

def migrate_database():
    """Migrate the existing database to support file-based documents."""
    
    db_path = "stealth_legal.db"
    
    if not os.path.exists(db_path):
        print("Database not found. Creating new database...")
        return
    
    print("Starting database migration...")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if migration is needed
        cursor.execute("PRAGMA table_info(documents)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'filename' in columns and 'file_path' in columns:
            print("Database already migrated. Skipping migration.")
            return
        
        print("Migrating database structure...")
        
        # Create backup of existing data
        cursor.execute("SELECT * FROM documents")
        existing_docs = cursor.fetchall()
        
        # Create new table structure
        cursor.execute("""
            CREATE TABLE documents_new (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                content TEXT,
                content_hash TEXT,
                etag TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX idx_documents_content ON documents_new(content)")
        cursor.execute("CREATE INDEX idx_documents_file_type ON documents_new(file_type)")
        cursor.execute("CREATE INDEX idx_documents_created_at ON documents_new(created_at)")
        
        # Migrate existing documents
        print(f"Migrating {len(existing_docs)} existing documents...")
        
        for doc in existing_docs:
            doc_id, title, content, etag, created_at, updated_at = doc
            
            # Generate filename and file path for existing text documents
            filename = f"document_{doc_id}.txt"
            file_path = f"uploads/migrated_{filename}"
            file_type = "txt"
            file_size = len(content.encode('utf-8')) if content else 0
            content_hash = hashlib.md5(content.encode()).hexdigest() if content else None
            
            # Insert into new table
            cursor.execute("""
                INSERT INTO documents_new 
                (id, title, filename, file_path, file_type, file_size, content, content_hash, etag, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (doc_id, title, filename, file_path, file_type, file_size, content, content_hash, etag, created_at, updated_at))
            
            # Create physical file for migrated documents
            uploads_dir = Path("uploads")
            uploads_dir.mkdir(exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content or "")
        
        # Drop old table and rename new one
        cursor.execute("DROP TABLE documents")
        cursor.execute("ALTER TABLE documents_new RENAME TO documents")
        
        # Commit changes
        conn.commit()
        
        print("Database migration completed successfully!")
        print(f"Migrated {len(existing_docs)} documents to file-based format")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
