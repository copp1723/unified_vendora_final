# VENDORA Docker Deployment Fix Guide

## Problem Diagnosis ✅
**Root Cause**: Your Docker image in Artifact Registry contains old code with `fastapi-mcp` import errors that prevent the container from starting.

**Evidence**: 
- Container fails to start and listen on port 8000
- You mentioned "Docker image was built before fastapi-mcp import fixes were applied"
- Error: "user-provided container failed to start and listen on the port"

## Solution: Rebuild & Redeploy with Fixed Code

### Step 1: Authentication (Do this first)
```bash
# Authenticate with your Google Cloud account
gcloud auth login

# Set your project
gcloud config set project vendora-464403

# Verify authentication
gcloud auth list
```

### Step 2: Rebuild Docker Image with Fixed Code
```bash
# Option A: Using Google Cloud Build (Recommended)
gcloud builds submit --tag gcr.io/vendora-464403/vendora-api .

# Option B: Using Docker (if available locally)
docker build -t gcr.io/vendora-464403/vendora-api .
docker push gcr.io/vendora-464403/vendora-api
```

### Step 3: Deploy to Cloud Run
```bash
# Deploy using gcloud CLI
gcloud run deploy vendora-backend \
    --image gcr.io/vendora-464403/vendora-api \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --port 8000 \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --max-instances 10 \
    --set-env-vars "PORT=8000,ENVIRONMENT=production"

# OR use your existing deploy script
./deploy.sh
```

### Step 4: Verify the Fix
```bash
# Check deployment status
gcloud run services describe vendora-backend --region=us-central1

# Test health endpoint
curl -f "$(gcloud run services describe vendora-backend --region=us-central1 --format='value(status.url)')/health"

# Check logs with new diagnostic output
gcloud logs read --service=vendora-backend --region=us-central1 --limit=50
```

## What I Fixed in the Code

### Enhanced Diagnostic Logging
- ✅ Added comprehensive startup logging to `src/main.py`
- ✅ Import validation for all dependencies
- ✅ Environment variable status logging
- ✅ FastAPI app creation tracking
- ✅ Server binding configuration validation
- ✅ Enhanced Docker CMD with verbose logging

### Key Changes Made:
1. **Import Error Handling**: Added try/catch around all imports with detailed logging
2. **Startup Validation**: Pre-flight checks for all critical components
3. **Configuration Logging**: Environment variable status (without exposing secrets)
4. **Health Check Logging**: Track when health endpoint is called
5. **Docker Logging**: Added verbose uvicorn flags for better container diagnostics

## Expected Results After Fix

### During Container Startup (New Logs):
```
🚀 VENDORA Container Startup - BEGIN
📍 Python executable: /usr/local/bin/python3
📍 Python version: 3.10.x
📍 Working directory: /home/appuser
📍 PORT environment variable: 8000
✅ FastAPI imports successful
✅ uvicorn import successful
✅ MailgunWebhookHandler import successful
🏗️ Creating FastAPI application...
✅ FastAPI app instance created
✅ CORS middleware added
✅ MailgunWebhookHandler initialized
✅ FastAPI application created successfully with all routes
📋 Configuration status: {...}
🚀 Creating FastAPI app instance...
✅ FastAPI app instance created successfully
📦 Module imported - app instance available for external server
```

### Healthy Deployment:
- Container starts within timeout
- Health check responds on `/health`
- Application listens on `0.0.0.0:8000`
- No import errors in logs

## Troubleshooting

### If Build Fails:
```bash
# Check build logs
gcloud builds log $(gcloud builds list --limit=1 --format="value(id)")
```

### If Deployment Still Fails:
```bash
# Check Cloud Run logs with new diagnostic output
gcloud logs read --service=vendora-backend --region=us-central1 --limit=100

# Check specific revision logs
gcloud logs read --service=vendora-backend --region=us-central1 \
    --filter="resource.labels.revision_name:vendora-backend-XXXXX"
```

### Common Issues:
1. **Authentication**: Run `gcloud auth login` first
2. **Missing Environment Variables**: Check Cloud Run environment variables
3. **Port Binding**: Ensure `PORT=8000` environment variable is set
4. **Import Errors**: New logging will show specific import failures

## Next Steps After Successful Deployment
1. Monitor application logs for any runtime issues
2. Test API endpoints: `/health`, `/api/v1/query`
3. Update frontend configuration if service URL changed
4. Set up monitoring alerts for container restart issues

---
**Note**: The diagnostic logging I added will help identify any remaining issues quickly. You should see much more detailed startup information in the Cloud Run logs after redeployment.