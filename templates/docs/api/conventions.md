# API Conventions


---

## URL Patterns

```
GET    /resources          # List
POST   /resources          # Create
GET    /resources/{id}     # Get one
PUT    /resources/{id}     # Update (full)
PATCH  /resources/{id}     # Update (partial)
DELETE /resources/{id}     # Delete
```

---

## Request/Response Format

**Success Response:**
```json
{
    "data": { ... },
    "meta": { "page": 1, "total": 100 }
}
```

**Error Response:**
```json
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid input",
        "details": { ... }
    }
}
```

---

## Status Codes

| Code | Usage |
|------|-------|
| 200 | Success |
| 201 | Created |
| 400 | Bad request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not found |
| 422 | Validation error |
| 500 | Server error |

---

## Pagination

```
GET /resources?page=1&per_page=20
```

---

## Filtering

```
GET /resources?status=active&created_after=2024-01-01
```

---

## Versioning

{Describe versioning strategy if applicable}
