# API Documentation

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication

All endpoints except `/auth/register` and `/auth/login` require JWT Bearer token.

```
Authorization: Bearer <access_token>
```

### Register
```http
POST /api/v1/auth/register
Content-Type: application/json

{
    "username": "researcher1",
    "email": "researcher@example.com",
    "password": "SecurePass123!"
}
```

Password requirements:
- Minimum 8 characters
- At least one uppercase letter
- At least one digit

### Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
    "username": "researcher1",
    "password": "SecurePass123!"
}
```

Response:
```json
{
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "token_type": "bearer",
    "expires_in": 1800
}
```

### Refresh Token
```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
    "refresh_token": "eyJ..."
}
```

## Domain Management

### Submit Domain for Analysis
```http
POST /api/v1/domains/analyze
Authorization: Bearer <token>
Content-Type: application/json

{
    "domain": "example.com",
    "source": "manual",
    "notes": "Research target"
}
```

Required role: RESEARCHER+

### Bulk Submit Domains
```http
POST /api/v1/domains/bulk
Authorization: Bearer <token>
Content-Type: application/json

{
    "domains": ["domain1.com", "domain2.com", "domain3.com"],
    "source": "dataset"
}
```

Required role: RESEARCHER+

### List Domains
```http
GET /api/v1/domains?page=1&page_size=20&search=example&classification=SUSPICIOUS&risk_level=HIGH&status=analyzed
Authorization: Bearer <token>
```

Required role: VIEWER+

### Get Domain Statistics
```http
GET /api/v1/domains/statistics
Authorization: Bearer <token>
```

### Get Domain Detail
```http
GET /api/v1/domains/{domain_id}
Authorization: Bearer <token>
```

### Update Domain
```http
PUT /api/v1/domains/{domain_id}
Authorization: Bearer <token>
Content-Type: application/json

{
    "classification": "GAMBLING_INDICATED",
    "risk_level": "HIGH",
    "notes": "Confirmed indicators"
}
```

Required role: RESEARCHER+

### Delete Domain
```http
DELETE /api/v1/domains/{domain_id}
Authorization: Bearer <token>
```

Required role: ADMIN

## Error Responses

All errors follow this format:
```json
{
    "error": "NotFoundError",
    "message": "Domain not found: <id>",
    "details": {}
}
```

Common HTTP status codes:
- `401` - Authentication required
- `403` - Insufficient permissions
- `404` - Resource not found
- `409` - Duplicate resource
- `422` - Validation error
- `429` - Rate limit exceeded
