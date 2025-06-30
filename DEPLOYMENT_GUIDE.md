# VENDORA Deployment Guide

## Quick Fix for Current Issues

The deployment failures were caused by:
1. **Missing `fastapi-mcp` package** - This package doesn't exist on PyPI
2. **Import errors** - The code was trying to import non-existent modules
3. **Incorrect entry point** - Docker was pointing to the wrong main file

## Fixed Issues

✅ **Removed fastapi-mcp dependency** from requirements.txt
✅ **Updated fastapi_main.py** to remove MCP imports
✅ **Fixed Dockerfile** to use correct entry point
✅ **Created simplified deployment option**

## Deployment Options

### Option 1: Quick Deploy (Recommended for immediate fix)

Use the simplified version for immediate deployment:

```bash
# Build with simplified Dockerfile
docker build -f Dockerfile.simple -t vendora-api-simple .

# Test locally
docker run -p 8000:8000 vendora-api-simple

# Deploy to Cloud Run
./deploy.sh
```

### Option 2: Full Application Deploy

After fixing the service dependencies:

```bash
# Build with main Dockerfile
docker build -t vendora-api .

# Deploy
./deploy.sh
```

## Environment Variables Required

For production deployment, set these environment variables:

```bash
# Required for basic functionality
export PORT=8000
export ENVIRONMENT=production

# Optional (for full functionality)
export GEMINI_API_KEY="your-gemini-key"
export OPENROUTER_API_KEY="your-openrouter-key"
export MAILGUN_PRIVATE_API_KEY="your-mailgun-key"
export MAILGUN_DOMAIN="your-domain"
export FIREBASE_PROJECT_ID="vendora-464403"
```

## Deployment Commands

### Using the deployment script:
```bash
chmod +x deploy.sh
./deploy.sh
```

### Manual deployment:
```bash
# Set project
gcloud config set project vendora-464403

# Build and push
docker build -t gcr.io/vendora-464403/vendora-api .
docker push gcr.io/vendora-464403/vendora-api

# Deploy to Cloud Run
gcloud run deploy vendora-api \
    --image gcr.io/vendora-464403/vendora-api \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --port 8000 \
    --memory 2Gi \
    --timeout 300
```

## Testing Deployment

After deployment, test these endpoints:

```bash
# Health check
curl https://your-service-url/health

# API status
curl https://your-service-url/api/v1/status

# Root endpoint
curl https://your-service-url/
```

## Next Steps

1. **Immediate**: Deploy with simplified version to get service running
2. **Short-term**: Fix service dependencies in the full application
3. **Long-term**: Implement proper MCP integration if needed

## Troubleshooting

### Container won't start
- Check logs: `gcloud logs read --service=vendora-api`
- Verify environment variables are set
- Test locally with Docker first

### Import errors
- Ensure all dependencies are in requirements.txt
- Check Python path configuration
- Verify file structure matches imports

### Timeout issues
- Increase Cloud Run timeout settings
- Optimize startup time
- Add proper health checks

## Service URLs

After deployment, your service will be available at:
- **Health**: `https://your-service-url/health`
- **API Docs**: `https://your-service-url/docs`
- **Status**: `https://your-service-url/api/v1/status`