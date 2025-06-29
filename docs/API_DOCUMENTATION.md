# VENDORA API Documentation

## Overview

The VENDORA API provides endpoints for automotive dealership analytics powered by a hierarchical multi-agent AI system. All endpoints (except health check) require Firebase authentication.

## Base URL

```
Production: https://api.vendora.com
Development: http://localhost:8000
```

## Authentication

All API requests must include a Firebase ID token in the Authorization header:

```
Authorization: Bearer YOUR_FIREBASE_ID_TOKEN
```

## Response Format

All responses follow a consistent structure using well-defined Pydantic models.

### Success Response

```json
{
  "data": {...},
  "metadata": {...}
}
```

### Error Response

```json
{
  "detail": {
    "error": "Error type",
    "message": "Detailed error message",
    "task_id": "TASK-12345678",  // Optional
    "suggestions": ["..."],       // Optional
    "quality_score": 0.85        // Optional
  }
}
```

## Endpoints

### Health Check

Check system health and component status.

**Endpoint:** `GET /health`  
**Authentication:** Not required  
**Response:**

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "components": {
    "flow_manager": true,
    "explainability_engine": true,
    "firebase_auth": true,
    "mcp_enabled": true
  },
  "version": "1.0.0"
}
```

### Process Query

Process an analytical query through the hierarchical agent system.

**Endpoint:** `POST /api/v1/query`  
**Authentication:** Required (verified email)  
**Request Body:**

```json
{
  "query": "What were my top selling vehicles last month?",
  "dealership_id": "dealer_123",
  "context": {
    "user_role": "sales_manager",
    "preferences": {
      "format": "detailed"
    }
  }
}
```

**Response:**

```json
{
  "summary": "Your top selling vehicles last month were F-150, Silverado, and RAV4",
  "detailed_insight": {
    "top_vehicles": [
      {"model": "F-150", "units_sold": 45, "revenue": 2250000},
      {"model": "Silverado", "units_sold": 38, "revenue": 1900000},
      {"model": "RAV4", "units_sold": 32, "revenue": 1120000}
    ],
    "total_sales": 285,
    "month_over_month_change": "+12.5%"
  },
  "data_visualization": {
    "type": "bar_chart",
    "config": {
      "x_axis": "vehicle_model",
      "y_axis": "units_sold",
      "title": "Top Selling Vehicles - Last Month"
    }
  },
  "confidence_level": "High",
  "data_sources": ["sales_transactions", "inventory"],
  "generated_at": "2024-01-15T10:30:00Z",
  "metadata": {
    "task_id": "TASK-1a2b3c4d",
    "complexity": "standard",
    "processing_time_ms": 1250,
    "revision_count": 0,
    "cached": false
  }
}
```

**Error Responses:**
- `400 Bad Request`: Invalid dealership_id format
- `403 Forbidden`: User doesn't have access to the specified dealership
- `422 Unprocessable Entity`: Query processing failed with details
- `504 Gateway Timeout`: Query processing timed out

### Get Task Status

Check the status of a specific analytical task.

**Endpoint:** `GET /api/v1/task/{task_id}/status`  
**Authentication:** Required  
**Path Parameters:**
- `task_id`: Task identifier (format: TASK-xxxxxxxx)

**Response:**

```json
{
  "task_id": "TASK-1a2b3c4d",
  "status": "approved",
  "current_level": 3,
  "complexity": "standard",
  "duration_ms": 1250,
  "draft_insights_count": 1,
  "has_validated_insight": true,
  "error_count": 0,
  "errors": []
}
```

**Status Values:**
- `pending`: Task created but not started
- `analyzing`: L1 Orchestrator analyzing the query
- `generating`: L2 Specialist generating insights
- `validating`: L3 Master Analyst validating results
- `approved`: Insight approved and ready
- `rejected`: Insight rejected by quality control
- `revision_needed`: Requires revision
- `delivered`: Delivered to user

### Get Agent Explanation

Get detailed explanation of a specific agent's activities.

**Endpoint:** `GET /api/v1/agent/{agent_id}/explanation`  
**Authentication:** Required  
**Path Parameters:**
- `agent_id`: One of `orchestrator`, `data_analyst`, `senior_analyst`, `master_analyst`

**Response:**

```json
{
  "agent_id": "data_analyst",
  "current_phase": "completing",
  "current_task": "Generating sales insight for dealer_123",
  "duration": "2 minutes 15 seconds",
  "summary": {
    "agent_id": "data_analyst",
    "phase": "completing",
    "current_task": "Generating sales insight for dealer_123",
    "duration_seconds": 135.2,
    "operations_count": 45,
    "files_accessed": 3,
    "errors_count": 0,
    "success_rate": 1.0
  },
  "operations": {
    "total": 45,
    "by_type": {
      "query_generation": 12,
      "data_analysis": 20,
      "insight_formatting": 13
    },
    "success_rate": 1.0,
    "total_duration_ms": 135200,
    "avg_duration_ms": 3004.4,
    "slow_operations": 2,
    "recent_operations": [...]
  },
  "files_modified": [],
  "decisions": [...],
  "errors": [],
  "timeline": [...],
  "recommendations": [
    "Consider caching frequently requested sales data",
    "Optimize SQL queries for large date ranges"
  ]
}
```

### Get System Overview

Get system-wide overview of all agents and operations.

**Endpoint:** `GET /api/v1/system/overview`  
**Authentication:** Required  

**Response:**

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "active_agents": 2,
  "total_agents": 4,
  "total_operations": 1523,
  "total_errors": 12,
  "error_rate": 0.0079,
  "active_agent_ids": ["orchestrator", "data_analyst"],
  "recent_operations": [...],
  "metrics": {
    "queries_processed": 245,
    "avg_response_time_ms": 1875
  }
}
```

### Get System Metrics

Get detailed system performance metrics.

**Endpoint:** `GET /api/v1/system/metrics`  
**Authentication:** Required (admin or analyst role)  

**Response:**

```json
{
  "flow_metrics": {
    "total_queries": 1250,
    "approved_insights": 1180,
    "rejected_insights": 70,
    "avg_processing_time_ms": 1452.3,
    "complexity_distribution": {
      "simple": 450,
      "standard": 650,
      "complex": 125,
      "critical": 25
    },
    "active_flows": 3,
    "total_flows": 1250,
    "approval_rate": 0.944,
    "cache_size": 150,
    "cache_hit_rate": "Not tracked"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Get Current User Info

Get information about the authenticated user.

**Endpoint:** `GET /api/v1/auth/me`  
**Authentication:** Required  

**Response:**

```json
{
  "uid": "user123",
  "email": "john.doe@dealership.com",
  "email_verified": true,
  "display_name": "John Doe",
  "dealership_id": "dealer_123",
  "roles": ["analyst", "manager"],
  "is_admin": false
}
```

### Mailgun Webhook

Process incoming emails from Mailgun (internal use).

**Endpoint:** `POST /api/v1/webhook/mailgun`  
**Authentication:** Mailgun signature verification  
**Content-Type:** `multipart/form-data` or `application/json`

**Response:**

```json
{
  "status": "processed",
  "message": "Email processed successfully"
}
```

## Rate Limiting

- Default: 100 requests per minute per user
- Query endpoint: 20 requests per minute per user
- Metrics endpoint: 10 requests per minute per user

## Data Models

### TaskComplexity Enum
- `simple`: Basic KPI lookup
- `standard`: Standard analysis
- `complex`: Complex forecasting, multi-year analysis
- `critical`: High-stakes decision support

### ConfidenceLevel Enum
- `Very High`: 95%+ confidence
- `High`: 85-95% confidence
- `Moderate`: 70-85% confidence
- `Low`: 50-70% confidence
- `Very Low`: Below 50% confidence

### VisualizationType Enum
- `line_chart`: Time series data
- `bar_chart`: Categorical comparisons
- `pie_chart`: Proportional data
- `table`: Tabular data
- `heatmap`: Multi-dimensional data
- `scatter_plot`: Correlation analysis

## Error Handling

The API uses standard HTTP status codes:

- `200 OK`: Success
- `400 Bad Request`: Invalid request format
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Business logic error
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service temporarily unavailable
- `504 Gateway Timeout`: Request timeout

## SDK Examples

### Python

```python
import requests

class VendoraClient:
    def __init__(self, api_url, firebase_token):
        self.api_url = api_url
        self.headers = {
            'Authorization': f'Bearer {firebase_token}',
            'Content-Type': 'application/json'
        }
    
    def process_query(self, query, dealership_id, context=None):
        response = requests.post(
            f'{self.api_url}/api/v1/query',
            headers=self.headers,
            json={
                'query': query,
                'dealership_id': dealership_id,
                'context': context or {}
            }
        )
        response.raise_for_status()
        return response.json()
```

### JavaScript/TypeScript

```typescript
class VendoraClient {
  constructor(
    private apiUrl: string,
    private getToken: () => Promise<string>
  ) {}

  async processQuery(
    query: string, 
    dealershipId: string, 
    context?: Record<string, any>
  ): Promise<QueryResponse> {
    const token = await this.getToken();
    const response = await fetch(`${this.apiUrl}/api/v1/query`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        query,
        dealership_id: dealershipId,
        context: context || {}
      })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail?.message || 'Request failed');
    }
    
    return response.json();
  }
}
```

## Webhook Integration

For Mailgun webhook integration, configure your Mailgun account to send webhooks to:

```
https://api.vendora.com/api/v1/webhook/mailgun
```

Ensure the webhook includes:
- Signature verification fields
- Email content and attachments
- Sender information

## Support

For API support, contact:
- Email: api-support@vendora.com
- Documentation: https://docs.vendora.com
- Status: https://status.vendora.com