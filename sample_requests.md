# Sample API Requests

This document contains sample requests for testing the Stealth Legal AI API.

## Base URL
```
http://localhost:8000
```

## 1. Create a Document

```bash
curl -X POST "http://localhost:8000/documents" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Sample Contract",
    "content": "This is a sample contract. The contract contains important terms and conditions that must be followed. The contract will be valid for one year from the date of signing."
  }'
```

**Response:**
```json
{
  "id": 1,
  "title": "Sample Contract",
  "content": "This is a sample contract. The contract contains important terms and conditions that must be followed. The contract will be valid for one year from the date of signing.",
  "etag": "\"a1b2c3d4e5f6\"",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": null
}
```

## 2. Get All Documents

```bash
curl -X GET "http://localhost:8000/documents?skip=0&limit=10"
```

## 3. Get Specific Document

```bash
curl -X GET "http://localhost:8000/documents/1"
```

## 4. Apply Text-based Changes (Redlining)

```bash
curl -X PATCH "http://localhost:8000/documents/1" \
  -H "Content-Type: application/json" \
  -H "If-Match: \"a1b2c3d4e5f6\"" \
  -d '{
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
  }'
```

## 5. Apply Range-based Changes

```bash
curl -X PATCH "http://localhost:8000/documents/1" \
  -H "Content-Type: application/json" \
  -H "If-Match: \"a1b2c3d4e5f6\"" \
  -d '{
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
  }'
```

## 6. Apply Multiple Changes

```bash
curl -X PATCH "http://localhost:8000/documents/1" \
  -H "Content-Type: application/json" \
  -H "If-Match: \"a1b2c3d4e5f6\"" \
  -d '{
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
          "text": "one year",
          "occurrence": 1
        },
        "replacement": "two years"
      }
    ]
  }'
```

## 7. Search Across All Documents

```bash
curl -X GET "http://localhost:8000/documents/search?q=contract&limit=10&offset=0"
```

**Response:**
```json
{
  "results": [
    {
      "document_id": 1,
      "title": "Sample Contract",
      "score": 2,
      "context": [
        "This is a sample contract. The contract contains important terms",
        "The contract will be valid for one year from the date of signing."
      ]
    }
  ],
  "total": 1,
  "limit": 10,
  "offset": 0
}
```

## 8. Search Within Specific Document

```bash
curl -X GET "http://localhost:8000/documents/1/search?q=terms&limit=5&offset=0"
```

## 9. Delete Document

```bash
curl -X DELETE "http://localhost:8000/documents/1"
```

## 10. Health Check

```bash
curl -X GET "http://localhost:8000/health"
```

**Response:**
```json
{
  "status": "healthy",
  "service": "Stealth Legal AI"
}
```

## Error Handling Examples

### 1. Document Not Found
```bash
curl -X GET "http://localhost:8000/documents/999"
```

**Response:**
```json
{
  "detail": "Document not found"
}
```

### 2. Concurrency Conflict (Wrong ETag)
```bash
curl -X PATCH "http://localhost:8000/documents/1" \
  -H "Content-Type: application/json" \
  -H "If-Match: \"wrong-etag\"" \
  -d '{
    "changes": [
      {
        "operation": "replace",
        "target": {"text": "contract", "occurrence": 1},
        "replacement": "agreement"
      }
    ]
  }'
```

**Response:**
```json
{
  "detail": "Document has been modified by another user"
}
```

### 3. Invalid Change Operation
```bash
curl -X PATCH "http://localhost:8000/documents/1" \
  -H "Content-Type: application/json" \
  -H "If-Match: \"a1b2c3d4e5f6\"" \
  -d '{
    "changes": [
      {
        "operation": "delete",
        "target": {"text": "contract", "occurrence": 1},
        "replacement": "agreement"
      }
    ]
  }'
```

**Response:**
```json
{
  "detail": "Unsupported operation: delete"
}
```

## Postman Collection

You can import these requests into Postman:

1. Create a new collection called "Stealth Legal AI"
2. Set the base URL variable to `http://localhost:8000`
3. Import the requests above
4. Use the `etag` from document responses in the `If-Match` header for PATCH requests

## Testing Large Documents

For testing with large documents, you can create a document with repeated content:

```bash
curl -X POST "http://localhost:8000/documents" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Large Document",
    "content": "This is a large document with repeated content. " 
  }' | jq -r '.id'
```

Then use the returned ID to test search and change operations on large content.
