#!/bin/bash
# Make script executable
chmod +x "$0"
# VENDORA Working Version Startup Script

echo "🚀 Starting VENDORA Working Version"
echo "=================================="

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

# Install working dependencies
echo "📚 Installing minimal dependencies..."
pip install -r working_requirements.txt

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Creating from working template..."
    cp working.env.example .env
    echo "✓ Created .env file from working.env.example"
    echo ""
    echo "🔑 IMPORTANT: Edit .env and add your GEMINI_API_KEY"
    echo "   Get your API key from: https://makersuite.google.com/app/apikey"
    echo ""
    read -p "Press Enter to continue after setting up your .env file..."
fi

# Check for Gemini API key
source .env
if [ -z "$GEMINI_API_KEY" ] || [ "$GEMINI_API_KEY" == "your-gemini-api-key-here" ]; then
    echo "❌ Error: GEMINI_API_KEY not configured in .env file"
    echo "   Please get your API key from: https://makersuite.google.com/app/apikey"
    echo "   Then edit .env and set GEMINI_API_KEY=your-actual-key"
    exit 1
fi

echo ""
echo "✅ All checks passed. Starting VENDORA Working Version..."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  VENDORA - Working Version"
echo "  Simplified but Functional AI Platform"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  🌐 API will be available at: http://localhost:8000"
echo "  📚 API Documentation: http://localhost:8000/docs"
echo "  ❤️  Health Check: http://localhost:8000/health"
echo ""
echo "  Key Endpoints:"
echo "  • POST /api/v1/query              - Process queries"
echo "  • GET  /api/v1/task/{id}/status   - Task status"
echo "  • GET  /api/v1/system/metrics     - System metrics"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Start the working application
python3 working_fastapi.py
