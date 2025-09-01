# Stealth Legal AI - Document Management Service

A full-stack document management service with advanced redlining capabilities and search functionality.

## Features

- **Document Management**: Create, read, update documents
- **Redlining/Change Requests**: Apply text changes with precise targeting
- **Advanced Search**: Full-text search across documents with context
- **Version Control**: ETag-based concurrency control
- **Bulk Operations**: Support for multiple changes in single request
- **Performance Optimized**: Handles large documents (10MB+) efficiently

## Tech Stack

- **Backend**: FastAPI (Python 3.11+)
- **Frontend**: React 18 + TypeScript + shadcn/ui
- **Database**: SQLite (production-ready for PostgreSQL)
- **Search**: In-memory inverted index
- **Testing**: pytest + React Testing Library

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- npm or yarn

### Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run backend
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Documents
- `GET /documents` - List all documents
- `POST /documents` - Create new document
- `GET /documents/{id}` - Get document by ID
- `PATCH /documents/{id}` - Apply changes to document
- `DELETE /documents/{id}` - Delete document

### Search
- `GET /documents/search` - Search across all documents
- `GET /documents/{id}/search` - Search within specific document

## Change Request Format

```json
{
  "changes": [
    {
      "operation": "replace",
      "target": {
        "text": "old text",
        "occurrence": 1
      },
      "replacement": "new text"
    }
  ]
}
```

## Performance Considerations

- **Large Documents**: Streaming processing for files >1MB
- **Search Index**: In-memory inverted index for O(log n) search
- **Concurrency**: ETag-based versioning prevents conflicts
- **Memory**: Efficient text processing with generators

## Testing

```bash
# Backend tests
pytest

# Frontend tests
cd frontend && npm test

# Performance tests
pytest tests/test_performance.py
```

## Architecture Decisions

- **FastAPI**: High performance, automatic OpenAPI docs, type safety
- **In-memory Search**: Simple, fast for prototype; easily replaceable with Elasticsearch
- **SQLite**: Simple setup, ACID compliance, easy migration to PostgreSQL
- **shadcn/ui**: Modern, accessible, customizable components
- **ETags**: Standard HTTP concurrency control mechanism
