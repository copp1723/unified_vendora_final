# VENDORA Working Version 🚀

A **clean, functional implementation** of the VENDORA automotive AI platform that actually works.

## What This Is

This is a **simplified but working** version of your VENDORA project that:
- ✅ Actually starts without errors
- ✅ Has a functional API
- ✅ Processes queries (with mock data or Gemini AI)
- ✅ Returns structured responses
- ✅ Has proper error handling
- ✅ Includes comprehensive testing

## Quick Start

### 1. Setup Environment
```bash
# Clone/navigate to the project
cd vendora_unified

# Copy environment template
cp working.env.example .env

# Edit .env and add your Gemini API key
# Get from: https://makersuite.google.com/app/apikey
nano .env
```

### 2. Install Dependencies
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install minimal requirements
pip install -r working_requirements.txt
```

### 3. Run the Application
```bash
# Option A: Use the startup script
chmod +x start_working.sh
./start_working.sh

# Option B: Run directly
python3 working_fastapi.py
```

### 4. Test It Works
```bash
# Run test suite
python3 test_working.py

# Or test manually
curl http://localhost:8000/health
```

## API Documentation

Once running, visit:
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **System Status**: http://localhost:8000/api/v1/system/status

### Key Endpoints

#### Process Query
```bash
POST /api/v1/query
{
  "query": "What were my top selling vehicles last month?",
  "dealership_id": "dealer_123",
  "context": {"user_role": "manager"}
}
```

#### Get Task Status
```bash
GET /api/v1/task/{task_id}/status
```

#### System Metrics
```bash
GET /api/v1/system/metrics
```

## Configuration

Edit `.env` file:

```bash
# Required: Your Gemini API key
GEMINI_API_KEY=your-key-here

# Optional settings
BIGQUERY_PROJECT=your-project
QUALITY_THRESHOLD=0.85
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=info
```

## Architecture

```
User Request → FastAPI → MinimalFlowManager → Gemini AI → Response
```

**Simple but effective:**
1. **FastAPI** handles HTTP requests/responses
2. **MinimalFlowManager** processes queries
3. **Gemini AI** generates insights (with fallback to mock data)
4. **Structured responses** with proper error handling

## What Works

- ✅ **HTTP API** with proper validation and error handling
- ✅ **Query Processing** through simplified hierarchical flow
- ✅ **Gemini Integration** with fallback to mock responses
- ✅ **Task Tracking** with status monitoring
- ✅ **System Metrics** and health monitoring
- ✅ **CORS Support** for frontend integration
- ✅ **Comprehensive Testing** with test suite

## What's Different from Original

**REMOVED (for now):**
- Complex multi-agent hierarchy (L1→L2→L3)
- Firebase authentication
- BigQuery integration
- Email processing
- Prometheus metrics
- Complex dependency hell

**SIMPLIFIED:**
- Single flow manager instead of multiple agents
- Direct Gemini API calls instead of complex orchestration
- Mock responses when APIs aren't available
- Minimal dependencies
- Clear error messages

## Extending This Version

### Add Authentication
```python
# Add to working_fastapi.py
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.post("/api/v1/query")
async def process_query(
    payload: QueryRequest,
    token: str = Depends(security)
):
    # Add your auth logic here
    ...
```

### Add Database
```python
# Add SQLAlchemy or similar
from sqlalchemy import create_engine
# Store tasks, metrics, etc.
```

### Add More AI Models
```python
# In minimal_flow_manager.py
async def _generate_openai_insight(self, task):
    # Add OpenAI integration
    pass

async def _generate_claude_insight(self, task):
    # Add Claude integration
    pass
```

## Testing

```bash
# Run all tests
python3 test_working.py

# Test individual components
python3 -c "
import asyncio
from minimal_flow_manager import MinimalFlowManager
asyncio.run(MinimalFlowManager({}).initialize())
print('✅ Flow Manager works')
"

# Test API
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Test query",
    "dealership_id": "test123"
  }'
```

## Deployment

### Local Development
```bash
# Already covered above
python3 working_fastapi.py
```

### Docker (Optional)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY working_requirements.txt .
RUN pip install -r working_requirements.txt
COPY working_fastapi.py minimal_flow_manager.py .env ./
CMD ["python", "working_fastapi.py"]
```

### Cloud Run / Similar
```bash
# Set environment variables in your cloud platform
GEMINI_API_KEY=your-key
PORT=8080

# Use working_fastapi.py as entry point
```

## Migration Path

To gradually migrate back to your full vision:

1. **Phase 1**: Get this working version deployed and tested
2. **Phase 2**: Add authentication (Firebase or simple JWT)
3. **Phase 3**: Add database persistence
4. **Phase 4**: Gradually add your L1→L2→L3 agent hierarchy
5. **Phase 5**: Add BigQuery, email processing, etc.

## Troubleshooting

### Import Errors
```bash
# Make sure you're in the right directory
cd vendora_unified

# Make sure virtual environment is activated
source venv/bin/activate

# Install requirements
pip install -r working_requirements.txt
```

### API Errors
```bash
# Check logs
python3 working_fastapi.py

# Check health endpoint
curl http://localhost:8000/health

# Verify .env file
cat .env | grep GEMINI_API_KEY
```

### Gemini API Issues
```bash
# Test your API key
python3 -c "
import google.generativeai as genai
genai.configure(api_key='your-key-here')
model = genai.GenerativeModel('gemini-pro')
print(model.generate_content('Hello').text)
"
```

## Next Steps

1. **Deploy this version** to see it working
2. **Add your real dealership data** (replace mock responses)
3. **Implement proper authentication**
4. **Add your complex agents gradually**
5. **Scale up as needed**

## Support

This working version is designed to be:
- **Debuggable**: Clear logs and error messages
- **Testable**: Comprehensive test suite
- **Extensible**: Easy to add features
- **Deployable**: Works in any Python environment

The goal is to give you a **solid foundation** that actually works, which you can then build upon to reach your full vision.

---

**Bottom Line**: This version **works**. Your original vision was solid, but the implementation was overengineered for the current state. Use this as a stepping stone to build back up to your full architecture, one piece at a time.
