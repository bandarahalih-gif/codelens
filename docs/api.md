# CodeLens REST API Documentation

## Overview

CodeLens exposes a REST API for programmatic code review integration. All endpoints accept and return JSON.

**Base URL:** `http://localhost:5000/api/v1`

## Authentication

API key authentication is optional for local development. For production, set the `CODELENS_API_KEY` environment variable and include it in requests:

```
Authorization: Bearer your-api-key
```

## Endpoints

### POST /api/v1/review

Create a new code review.

**Request Body:**
```json
{
    "code": "def hello():\n    print('world')",
    "filename": "hello.py",
    "language": "python"
}
```

**Response (201):**
```json
{
    "id": 1,
    "filename": "hello.py",
    "language": "python",
    "status": "complete",
    "total_findings": 2,
    "critical": 0,
    "high": 1,
    "medium": 1,
    "low": 0,
    "tokens_used": 4500,
    "analysis_time_ms": 1200,
    "created_at": "2026-05-15T10:30:00",
    "completed_at": "2026-05-15T10:30:01"
}
```

### GET /api/v1/reviews

List recent reviews.

**Query Parameters:**
- `limit` (int, default: 20) — Maximum number of reviews to return

### GET /api/v1/reviews/:id

Get a specific review with all findings.

**Response includes:** All review fields plus `findings` array.

### GET /api/v1/stats

Get usage statistics.

**Response:**
```json
{
    "today": {"total_tokens": 50000, "review_count": 5},
    "week": {"total_tokens": 350000, "review_count": 35},
    "all_time": {"total_reviews": 150, "total_tokens": 1500000}
}
```

## Error Responses

All errors return JSON:
```json
{
    "error": "Human-readable error message"
}
```

## Rate Limits

- 100 requests per minute per IP
- Token budget enforced per daily limit (configurable)
