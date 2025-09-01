import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import get_db
from app.models import Base, Document
from app.schemas import DocumentCreate, ChangeOperation, ChangeTarget, ChangeRange
from app.services import DocumentService
from fastapi.testclient import TestClient
from app.main import app

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
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

@pytest.fixture(scope="function")
def setup_database():
    """Setup test database before each test."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def sample_document():
    """Sample document data for testing."""
    return {
        "title": "Test Contract",
        "content": "This is a test contract. The contract contains important terms and conditions."
    }

@pytest.fixture
def large_document():
    """Large document for performance testing."""
    content = "This is a large document. " * 10000  # ~300KB
    return {
        "title": "Large Document",
        "content": content
    }

class TestDocumentCRUD:
    """Test basic CRUD operations."""
    
    def test_create_document(self, setup_database, sample_document):
        """Test document creation."""
        response = client.post("/documents", json=sample_document)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == sample_document["title"]
        assert data["content"] == sample_document["content"]
        assert "id" in data
        assert "etag" in data
    
    def test_get_document(self, setup_database, sample_document):
        """Test retrieving a document."""
        # Create document
        create_response = client.post("/documents", json=sample_document)
        doc_id = create_response.json()["id"]
        
        # Get document
        response = client.get(f"/documents/{doc_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == sample_document["title"]
        assert data["content"] == sample_document["content"]
    
    def test_get_nonexistent_document(self, setup_database):
        """Test getting a document that doesn't exist."""
        response = client.get("/documents/999")
        assert response.status_code == 404
    
    def test_list_documents(self, setup_database, sample_document):
        """Test listing documents."""
        # Create multiple documents
        client.post("/documents", json=sample_document)
        client.post("/documents", json={"title": "Doc 2", "content": "Content 2"})
        
        response = client.get("/documents")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
    
    def test_delete_document(self, setup_database, sample_document):
        """Test document deletion."""
        # Create document
        create_response = client.post("/documents", json=sample_document)
        doc_id = create_response.json()["id"]
        
        # Delete document
        response = client.delete(f"/documents/{doc_id}")
        assert response.status_code == 204
        
        # Verify document is deleted
        get_response = client.get(f"/documents/{doc_id}")
        assert get_response.status_code == 404

class TestDocumentChanges:
    """Test document change/redlining operations."""
    
    def test_replace_text_by_occurrence(self, setup_database, sample_document):
        """Test replacing text by finding specific occurrence."""
        # Create document
        create_response = client.post("/documents", json=sample_document)
        doc_id = create_response.json()["id"]
        etag = create_response.json()["etag"]
        
        # Apply changes
        changes = {
            "changes": [
                {
                    "operation": "replace",
                    "target": {
                        "text": "contract",
                        "occurrence": 1
                    },
                    "replacement": "agreement"
                }
            ]
        }
        
        response = client.patch(
            f"/documents/{doc_id}",
            json=changes,
            headers={"If-Match": etag}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "agreement" in data["content"]
        assert "contract" not in data["content"]
    
    def test_replace_by_range(self, setup_database, sample_document):
        """Test replacing text by character range."""
        # Create document
        create_response = client.post("/documents", json=sample_document)
        doc_id = create_response.json()["id"]
        etag = create_response.json()["etag"]
        
        # Apply changes
        changes = {
            "changes": [
                {
                    "operation": "replace",
                    "range": {
                        "start": 0,
                        "end": 4
                    },
                    "replacement": "That"
                }
            ]
        }
        
        response = client.patch(
            f"/documents/{doc_id}",
            json=changes,
            headers={"If-Match": etag}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["content"].startswith("That is a test")
    
    def test_multiple_changes(self, setup_database, sample_document):
        """Test applying multiple changes in one request."""
        # Create document
        create_response = client.post("/documents", json=sample_document)
        doc_id = create_response.json()["id"]
        etag = create_response.json()["etag"]
        
        # Apply multiple changes
        changes = {
            "changes": [
                {
                    "operation": "replace",
                    "target": {
                        "text": "contract",
                        "occurrence": 1
                    },
                    "replacement": "agreement"
                },
                {
                    "operation": "replace",
                    "target": {
                        "text": "test",
                        "occurrence": 1
                    },
                    "replacement": "sample"
                }
            ]
        }
        
        response = client.patch(
            f"/documents/{doc_id}",
            json=changes,
            headers={"If-Match": etag}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "agreement" in data["content"]
        assert "sample" in data["content"]
    
    def test_concurrency_control(self, setup_database, sample_document):
        """Test ETag-based concurrency control."""
        # Create document
        create_response = client.post("/documents", json=sample_document)
        doc_id = create_response.json()["id"]
        etag = create_response.json()["etag"]
        
        # First change
        changes1 = {
            "changes": [
                {
                    "operation": "replace",
                    "target": {"text": "contract", "occurrence": 1},
                    "replacement": "agreement"
                }
            ]
        }
        
        response1 = client.patch(
            f"/documents/{doc_id}",
            json=changes1,
            headers={"If-Match": etag}
        )
        assert response.status_code == 200
        
        # Second change with old ETag should fail
        changes2 = {
            "changes": [
                {
                    "operation": "replace",
                    "target": {"text": "test", "occurrence": 1},
                    "replacement": "sample"
                }
            ]
        }
        
        response2 = client.patch(
            f"/documents/{doc_id}",
            json=changes2,
            headers={"If-Match": etag}  # Old ETag
        )
        assert response.status_code == 412  # Precondition Failed
    
    def test_invalid_change_operations(self, setup_database, sample_document):
        """Test invalid change operations."""
        # Create document
        create_response = client.post("/documents", json=sample_document)
        doc_id = create_response.json()["id"]
        etag = create_response.json()["etag"]
        
        # Test invalid operation
        changes = {
            "changes": [
                {
                    "operation": "delete",  # Unsupported operation
                    "target": {"text": "contract", "occurrence": 1},
                    "replacement": "agreement"
                }
            ]
        }
        
        response = client.patch(
            f"/documents/{doc_id}",
            json=changes,
            headers={"If-Match": etag}
        )
        assert response.status_code == 400
        
        # Test missing target and range
        changes = {
            "changes": [
                {
                    "operation": "replace",
                    "replacement": "agreement"
                }
            ]
        }
        
        response = client.patch(
            f"/documents/{doc_id}",
            json=changes,
            headers={"If-Match": etag}
        )
        assert response.status_code == 400

class TestSearchFunctionality:
    """Test search functionality."""
    
    def test_search_across_documents(self, setup_database):
        """Test searching across all documents."""
        # Create multiple documents
        doc1 = {"title": "Contract A", "content": "This contract contains terms about payment"}
        doc2 = {"title": "Contract B", "content": "This agreement has different terms"}
        
        client.post("/documents", json=doc1)
        client.post("/documents", json=doc2)
        
        # Search for "contract"
        response = client.get("/documents/search?q=contract")
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) > 0
        
        # Search for "terms"
        response = client.get("/documents/search?q=terms")
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 2  # Both documents contain "terms"
    
    def test_search_within_document(self, setup_database, sample_document):
        """Test searching within a specific document."""
        # Create document
        create_response = client.post("/documents", json=sample_document)
        doc_id = create_response.json()["id"]
        
        # Search within document
        response = client.get(f"/documents/{doc_id}/search?q=contract")
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) > 0
        assert data["results"][0]["document_id"] == doc_id
    
    def test_search_pagination(self, setup_database):
        """Test search pagination."""
        # Create multiple documents
        for i in range(5):
            doc = {
                "title": f"Document {i}",
                "content": f"This is document {i} with contract terms"
            }
            client.post("/documents", json=doc)
        
        # Search with limit
        response = client.get("/documents/search?q=contract&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) <= 2
        assert data["limit"] == 2
    
    def test_search_empty_query(self, setup_database):
        """Test search with empty query."""
        response = client.get("/documents/search?q=")
        assert response.status_code == 422  # Validation error

class TestPerformance:
    """Test performance with large documents."""
    
    def test_large_document_creation(self, setup_database, large_document):
        """Test creating a large document."""
        response = client.post("/documents", json=large_document)
        assert response.status_code == 201
        data = response.json()
        assert len(data["content"]) > 100000  # Verify large content
    
    def test_large_document_search(self, setup_database, large_document):
        """Test searching in large document."""
        # Create large document
        create_response = client.post("/documents", json=large_document)
        doc_id = create_response.json()["id"]
        
        # Search in large document
        response = client.get(f"/documents/{doc_id}/search?q=document")
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) > 0
    
    def test_large_document_changes(self, setup_database, large_document):
        """Test applying changes to large document."""
        # Create large document
        create_response = client.post("/documents", json=large_document)
        doc_id = create_response.json()["id"]
        etag = create_response.json()["etag"]
        
        # Apply changes
        changes = {
            "changes": [
                {
                    "operation": "replace",
                    "target": {"text": "large document", "occurrence": 1},
                    "replacement": "big document"
                }
            ]
        }
        
        response = client.patch(
            f"/documents/{doc_id}",
            json=changes,
            headers={"If-Match": etag}
        )
        assert response.status_code == 200
