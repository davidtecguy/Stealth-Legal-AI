import pytest
import time
import random
import string
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import get_db
from app.models import Base, Document
from app.services import DocumentService
from fastapi.testclient import TestClient
from app.main import app

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_performance.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def generate_large_content(size_mb=10):
    """Generate large content for performance testing."""
    # Generate ~1MB of content
    chunk = "This is a large document with repeated content for performance testing. " * 1000
    chunks_needed = size_mb
    return chunk * chunks_needed

def generate_searchable_content():
    """Generate content with searchable terms."""
    terms = ["contract", "agreement", "terms", "conditions", "payment", "liability", "confidentiality"]
    content = []
    for _ in range(1000):
        term = random.choice(terms)
        sentence = f"This document contains {term} and other legal provisions. "
        content.append(sentence)
    return "".join(content)

class TestPerformance:
    """Performance tests for large documents and search operations."""
    
    @pytest.fixture(autoscope="class")
    def setup_database(self):
        """Setup test database."""
        Base.metadata.create_all(bind=engine)
        yield
        Base.metadata.drop_all(bind=engine)
    
    def test_large_document_creation_performance(self, setup_database):
        """Test creating large documents (10MB+)."""
        large_content = generate_large_content(10)  # 10MB
        
        start_time = time.time()
        response = client.post("/documents", json={
            "title": "Large Performance Test Document",
            "content": large_content
        })
        end_time = time.time()
        
        assert response.status_code == 201
        creation_time = end_time - start_time
        
        # Should complete within 5 seconds for 10MB document
        assert creation_time < 5.0, f"Document creation took {creation_time:.2f}s, expected < 5s"
        
        data = response.json()
        assert len(data["content"]) > 10000000  # Verify large content
    
    def test_large_document_search_performance(self, setup_database):
        """Test search performance on large documents."""
        # Create large document with searchable content
        searchable_content = generate_searchable_content()
        
        response = client.post("/documents", json={
            "title": "Searchable Large Document",
            "content": searchable_content
        })
        assert response.status_code == 201
        doc_id = response.json()["id"]
        
        # Test search performance
        start_time = time.time()
        search_response = client.get(f"/documents/{doc_id}/search?q=contract&limit=10")
        end_time = time.time()
        
        assert search_response.status_code == 200
        search_time = end_time - start_time
        
        # Search should complete within 1 second
        assert search_time < 1.0, f"Search took {search_time:.2f}s, expected < 1s"
        
        data = search_response.json()
        assert len(data["results"]) > 0
    
    def test_bulk_search_performance(self, setup_database):
        """Test search performance across multiple large documents."""
        # Create multiple documents
        doc_ids = []
        for i in range(5):
            content = generate_searchable_content()
            response = client.post("/documents", json={
                "title": f"Bulk Search Document {i}",
                "content": content
            })
            assert response.status_code == 201
            doc_ids.append(response.json()["id"])
        
        # Test bulk search performance
        start_time = time.time()
        search_response = client.get("/documents/search?q=contract&limit=20")
        end_time = time.time()
        
        assert search_response.status_code == 200
        search_time = end_time - start_time
        
        # Bulk search should complete within 2 seconds
        assert search_time < 2.0, f"Bulk search took {search_time:.2f}s, expected < 2s"
        
        data = search_response.json()
        assert len(data["results"]) > 0
    
    def test_large_document_change_performance(self, setup_database):
        """Test applying changes to large documents."""
        # Create large document
        large_content = generate_large_content(5)  # 5MB
        response = client.post("/documents", json={
            "title": "Large Change Test Document",
            "content": large_content
        })
        assert response.status_code == 201
        
        doc_data = response.json()
        doc_id = doc_data["id"]
        etag = doc_data["etag"]
        
        # Test change application performance
        start_time = time.time()
        change_response = client.patch(f"/documents/{doc_id}", 
            headers={"If-Match": etag},
            json={
                "changes": [
                    {
                        "operation": "replace",
                        "target": {
                            "text": "large document",
                            "occurrence": 1
                        },
                        "replacement": "modified large document"
                    }
                ]
            }
        )
        end_time = time.time()
        
        assert change_response.status_code == 200
        change_time = end_time - start_time
        
        # Change should complete within 3 seconds
        assert change_time < 3.0, f"Change application took {change_time:.2f}s, expected < 3s"
    
    def test_concurrent_operations_performance(self, setup_database):
        """Test performance under concurrent operations."""
        import threading
        import concurrent.futures
        
        # Create base document
        response = client.post("/documents", json={
            "title": "Concurrent Test Document",
            "content": "This is a test document for concurrent operations."
        })
        assert response.status_code == 201
        doc_id = response.json()["id"]
        
        def perform_search():
            """Perform search operation."""
            search_response = client.get(f"/documents/{doc_id}/search?q=test&limit=5")
            return search_response.status_code == 200
        
        def perform_read():
            """Perform read operation."""
            read_response = client.get(f"/documents/{doc_id}")
            return read_response.status_code == 200
        
        # Test concurrent operations
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            search_futures = [executor.submit(perform_search) for _ in range(5)]
            read_futures = [executor.submit(perform_read) for _ in range(5)]
            
            # Wait for all operations to complete
            search_results = [future.result() for future in search_futures]
            read_results = [future.result() for future in read_futures]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # All operations should complete within 5 seconds
        assert total_time < 5.0, f"Concurrent operations took {total_time:.2f}s, expected < 5s"
        assert all(search_results), "All search operations should succeed"
        assert all(read_results), "All read operations should succeed"
    
    def test_memory_usage_performance(self, setup_database):
        """Test memory usage with large documents."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create multiple large documents
        for i in range(3):
            large_content = generate_large_content(2)  # 2MB each
            response = client.post("/documents", json={
                "title": f"Memory Test Document {i}",
                "content": large_content
            })
            assert response.status_code == 201
        
        # Perform operations
        for _ in range(10):
            search_response = client.get("/documents/search?q=document&limit=10")
            assert search_response.status_code == 200
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (< 100MB for 6MB of documents + operations)
        assert memory_increase < 100, f"Memory increased by {memory_increase:.2f}MB, expected < 100MB"
    
    def test_search_index_performance(self, setup_database):
        """Test search index performance with many documents."""
        # Create many documents with searchable content
        for i in range(50):
            content = generate_searchable_content()
            response = client.post("/documents", json={
                "title": f"Index Test Document {i}",
                "content": content
            })
            assert response.status_code == 201
        
        # Test search performance with large index
        start_time = time.time()
        search_response = client.get("/documents/search?q=contract&limit=20")
        end_time = time.time()
        
        assert search_response.status_code == 200
        search_time = end_time - start_time
        
        # Search should still be fast even with many documents
        assert search_time < 1.0, f"Search with large index took {search_time:.2f}s, expected < 1s"
        
        data = search_response.json()
        assert len(data["results"]) > 0
    
    def test_etag_generation_performance(self, setup_database):
        """Test ETag generation performance for large documents."""
        large_content = generate_large_content(5)  # 5MB
        
        start_time = time.time()
        response = client.post("/documents", json={
            "title": "ETag Performance Test",
            "content": large_content
        })
        end_time = time.time()
        
        assert response.status_code == 201
        etag_time = end_time - start_time
        
        # ETag generation should be fast
        assert etag_time < 2.0, f"ETag generation took {etag_time:.2f}s, expected < 2s"
        
        data = response.json()
        assert data["etag"] is not None
        assert data["etag"].startswith('"') and data["etag"].endswith('"')

if __name__ == "__main__":
    # Run performance tests
    pytest.main([__file__, "-v", "-s"])
