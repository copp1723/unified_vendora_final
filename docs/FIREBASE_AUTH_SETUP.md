# Firebase Authentication Setup Guide

This guide explains how to set up and use Firebase Authentication with the VENDORA FastAPI backend.

## Overview

The VENDORA platform uses Firebase Authentication to secure API endpoints. This implementation:

- Verifies Firebase ID tokens sent in the Authorization header
- Protects all API endpoints (except health and public endpoints)
- Supports role-based access control (RBAC)
- Validates dealership access permissions
- Works seamlessly with Google Cloud services

## Architecture

```
Frontend (React) → Firebase Auth → ID Token → FastAPI Backend → Verify Token → Access Granted/Denied
```

## Setup Instructions

### 1. Firebase Project Setup

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project or select existing one
3. Enable Authentication:
   - Go to Authentication → Sign-in method
   - Enable Email/Password (and any other providers you need)

### 2. Service Account Setup

1. In Firebase Console, go to Project Settings → Service Accounts
2. Click "Generate new private key"
3. Save the JSON file securely
4. Set the path in your `.env` file:
   ```
   FIREBASE_SERVICE_ACCOUNT_PATH=/path/to/serviceAccount.json
   ```

### 3. Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# Firebase Configuration
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_SERVICE_ACCOUNT_PATH=/path/to/firebase-service-account.json

# Other required variables...
GEMINI_API_KEY=your-gemini-api-key
BIGQUERY_PROJECT=your-bigquery-project
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

## Authentication Flow

### 1. Frontend Authentication

The frontend (React) authenticates users using Firebase SDK:

```javascript
import { signInWithEmailAndPassword } from 'firebase/auth';

const userCredential = await signInWithEmailAndPassword(auth, email, password);
const idToken = await userCredential.user.getIdToken();
```

### 2. API Requests with Token

Include the ID token in the Authorization header:

```javascript
const response = await fetch('https://api.vendora.com/api/v1/query', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${idToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    query: "What were my top selling vehicles?",
    dealership_id: "dealer_123"
  })
});
```

### 3. Backend Token Verification

The FastAPI backend automatically verifies tokens using dependencies:

```python
@app.post("/api/v1/query")
async def process_query(
    payload: QueryRequest,
    current_user: FirebaseUser = Depends(get_current_verified_user)
):
    # current_user is automatically populated with verified user data
    # Access is already validated
```

## Protected Endpoints

All API endpoints are protected by default and require authentication:

- `POST /api/v1/query` - Requires verified email
- `GET /api/v1/task/{task_id}/status` - Requires authentication
- `GET /api/v1/agent/{agent_id}/explanation` - Requires authentication
- `GET /api/v1/system/overview` - Requires authentication
- `GET /api/v1/system/metrics` - Requires admin or analyst role
- `GET /api/v1/auth/me` - Returns current user info

## Custom Claims and Roles

### Setting Custom Claims

Custom claims can be set using the Firebase Admin SDK:

```python
from src.auth.firebase_auth import get_firebase_auth_handler

auth_handler = get_firebase_auth_handler()
await auth_handler.set_custom_claims(uid, {
    'dealership_id': 'dealer_123',
    'roles': ['analyst', 'manager'],
    'admin': False
})
```

### Available Custom Claims

- `dealership_id`: Associates user with a specific dealership
- `roles`: List of user roles (e.g., ['analyst', 'manager'])
- `admin`: Boolean flag for admin users

### Role-Based Access Control

Use the `RequireRole` dependency for role-based endpoints:

```python
@app.get("/api/v1/admin/users")
async def get_all_users(
    current_user: FirebaseUser = Depends(RequireRole(["admin"]))
):
    # Only users with 'admin' role can access
```

## Dealership Access Control

The system automatically validates dealership access:

```python
# In the /api/v1/query endpoint
if not current_user.custom_claims.get('admin', False):
    if current_user.dealership_id != payload.dealership_id:
        # Access denied - user can only query their own dealership
```

Admins can access all dealerships.

## Testing Authentication

### 1. Get Current User Info

```bash
curl -H "Authorization: Bearer YOUR_ID_TOKEN" \
  https://api.vendora.com/api/v1/auth/me
```

### 2. Test Protected Endpoint

```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_ID_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "dealership_id": "dealer_123"}' \
  https://api.vendora.com/api/v1/query
```

## Error Responses

### 401 Unauthorized
- Invalid or expired token
- Token signature verification failed

### 403 Forbidden
- Email not verified (for endpoints requiring verified email)
- Insufficient roles
- Dealership access denied

### Example Error Response

```json
{
  "detail": {
    "error": "Access denied",
    "message": "You don't have access to dealership dealer_456"
  }
}
```

## Security Best Practices

1. **Token Refresh**: ID tokens expire after 1 hour. Implement token refresh on the frontend:
   ```javascript
   if (tokenExpiringSoon) {
     const newToken = await user.getIdToken(true);
   }
   ```

2. **HTTPS Only**: Always use HTTPS in production

3. **CORS Configuration**: Configure CORS appropriately in production

4. **Service Account Security**: Keep service account keys secure and never commit to git

5. **Custom Claims**: Limit custom claims size (max 1000 bytes)

## Troubleshooting

### "Firebase auth handler not initialized"
- Check that `FIREBASE_PROJECT_ID` is set in environment
- Verify service account file exists and is readable
- Check startup logs for initialization errors

### "Invalid authentication token"
- Ensure token is included in Authorization header as `Bearer TOKEN`
- Check if token has expired (tokens expire after 1 hour)
- Verify Firebase project ID matches between frontend and backend

### "Email verification required"
- User must verify their email through Firebase Auth
- Use `get_current_user` instead of `get_current_verified_user` if email verification not required

## Development Mode

For local development without Firebase:

1. Set `ENVIRONMENT=development` in `.env`
2. The system will log warnings but continue to run
3. Authentication will be bypassed (not recommended for testing auth flows)

## Integration with Google Cloud

Firebase Authentication works seamlessly with other Google Cloud services:

- Uses same project ID as BigQuery
- Can share service accounts (with appropriate permissions)
- Integrated logging and monitoring

## Next Steps

1. Configure frontend to use Firebase Auth
2. Set up user registration flow
3. Implement password reset functionality
4. Configure additional authentication providers (Google, Microsoft, etc.)
5. Set up custom claims for your users
6. Implement role management UI