#!/bin/bash
# VENDORA Platform Startup Script

echo "🚀 Starting VENDORA Platform with Hierarchical Flow"
echo "=================================================="

# Check Python version
python_version=$(python3 --version 2>&1)
echo "✓ Python version: $python_version"

# Check for virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cat > .env << EOL
# VENDORA Environment Configuration

# Google Cloud Configuration
GEMINI_API_KEY=your-gemini-api-key
BIGQUERY_PROJECT=your-bigquery-project
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json

# Quality Configuration
QUALITY_THRESHOLD=0.85

# Storage Configuration
DATA_STORAGE_PATH=./data
MEMORY_STORAGE_PATH=./memory

# Logging
LOG_TO_FILE=true
EOL
    echo "✓ Created .env file. Please update with your API keys."
    exit 1
fi

# Create necessary directories
echo "📁 Creating data directories..."
mkdir -p data
mkdir -p memory
mkdir -p logs/agent_activity

# Export environment variables
export $(cat .env | grep -v '^#' | xargs)

# Check for required API keys
if [ -z "$GEMINI_API_KEY" ] || [ "$GEMINI_API_KEY" == "your-gemini-api-key" ]; then
    echo "❌ Error: GEMINI_API_KEY not configured in .env file"
    echo "   Please get your API key from: https://makersuite.google.com/app/apikey"
    exit 1
fi

# Run the application
echo ""
echo "✅ All checks passed. Starting VENDORA..."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  VENDORA - Automotive AI Data Platform"
echo "  Hierarchical Multi-Agent Architecture Active"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  API Endpoints:"
echo "  • POST   /api/v1/query              - Process query"
echo "  • GET    /api/v1/task/<id>/status   - Task status"
echo "  • GET    /api/v1/system/metrics     - Metrics"
echo "  • GET    /api/v1/system/overview    - Overview"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Start the main application
python3 src/main.py
