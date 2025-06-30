"""
Working VENDORA FastAPI - Basic Version (No Cloud Dependencies)
"""

import asyncio
import logging
import uvicorn
from datetime import datetime
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Simple flow manager without Google dependencies
class BasicFlowManager:
    def __init__(self):
        self.metrics = {"total_queries": 0, "successful_queries": 0}
    
    async def initialize(self):
        logger.info("✅ Basic Flow Manager initialized")
    
    async def process_user_query(self, query: str, dealership_id: str, user_context: Dict = None):
        self.metrics["total_queries"] += 1
        
        # Basic response without external dependencies
        response = {
            "summary": f"Analysis complete for dealership {dealership_id}",
            "detailed_insight": {
                "query": query,
                "analysis": "Basic automotive business intelligence response",
                "recommendations": ["Monitor sales trends", "Optimize inventory", "Improve customer experience"]
            },
            "confidence_level": "MEDIUM",
            "data_sources": ["sample_data"],
            "generated_at": datetime.now(),
            "metadata": {
                "processing_time_ms": 150,
                "agent_type": "basic_flow",
                "cloud_integration": "disabled"
            }
        }
        
        self.metrics["successful_queries"] += 1
        return response
    
    async def get_metrics(self):
        return {
            **self.metrics,
            "success_rate": self.metrics["successful_queries"] / max(self.metrics["total_queries"], 1),
            "system_status": "operational_basic"
        }
    
    async def shutdown(self):
        logger.info("🛑 Basic Flow Manager shutdown")

# Global instance
flow_manager: Optional[BasicFlowManager] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup application lifecycle"""
    global flow_manager
    
    logger.info("🚀 Starting VENDORA Basic Platform")
    
    try:
        flow_manager = BasicFlowManager()
        await flow_manager.initialize()
        logger.info("🎉 VENDORA Basic Platform Ready!")
    except Exception as e:
        logger.error(f"❌ Startup failed: {str(e)}")
        raise
    
    yield
    
    # Cleanup
    logger.info("🛑 Shutting down VENDORA Basic Platform")
    if flow_manager:
        await flow_manager.shutdown()

# Create FastAPI app
app = FastAPI(
    title="VENDORA AI Platform - Basic Edition",
    description="AI-Powered Automotive Business Intelligence (Basic Version)",
    version="1.5.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class QueryRequest(BaseModel):
    query: str = Field(..., description="User query about automotive business")
    dealership_id: str = Field(..., description="Dealership identifier")
    user_context: Optional[Dict[str, Any]] = Field(default=None, description="Additional user context")

# Health check endpoints
@app.get("/", tags=["Health"])
async def root():
    """Root endpoint with system status"""
    return {
        "message": "VENDORA AI Platform - Basic Edition",
        "status": "operational",
        "version": "1.5.0",
        "mode": "basic",
        "timestamp": datetime.now(),
        "features": [
            "Basic Analytics",
            "Sample Data Processing",
            "FastAPI Framework",
            "No External Dependencies"
        ]
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "services": {
            "flow_manager": flow_manager is not None,
            "mode": "basic",
            "cloud_integration": "disabled"
        }
    }

# Core analytics endpoint
@app.post("/analyze", tags=["Analytics"])
async def analyze_query(request: QueryRequest):
    """Process business intelligence query"""
    try:
        if not flow_manager:
            raise HTTPException(status_code=503, detail="Flow manager not initialized")
        
        logger.info(f"🔍 Processing query: {request.query}")
        result = await flow_manager.process_user_query(
            request.query,
            request.dealership_id,
            request.user_context or {}
        )
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/metrics", tags=["Analytics"])
async def get_system_metrics():
    """Get system performance metrics"""
    try:
        if not flow_manager:
            raise HTTPException(status_code=503, detail="Flow manager not initialized")
        
        metrics = await flow_manager.get_metrics()
        return metrics
        
    except Exception as e:
        logger.error(f"❌ Metrics collection failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Metrics failed: {str(e)}")

# Demo endpoints
@app.get("/demo/sample-query", tags=["Demo"])
async def demo_sample_query():
    """Demo endpoint with sample automotive queries"""
    sample_queries = [
        "What were our best selling vehicles last month?",
        "How is our inventory performing compared to last quarter?",
        "Show me customer conversion rates by lead source",
        "What's the average time vehicles spend on the lot?",
        "Analyze our service department revenue trends"
    ]
    
    return {
        "message": "Sample automotive business queries",
        "queries": sample_queries,
        "usage": "POST /analyze with one of these queries",
        "example_request": {
            "query": sample_queries[0],
            "dealership_id": "DEMO_DEALERSHIP_001"
        }
    }

@app.get("/demo/quick-test", tags=["Demo"])
async def demo_quick_test():
    """Quick test of the system"""
    try:
        test_request = QueryRequest(
            query="Show me our top performing vehicles",
            dealership_id="DEMO_DEALERSHIP"
        )
        
        result = await analyze_query(test_request)
        
        return {
            "demo_test": "completed",
            "status": "success",
            "sample_result": result,
            "message": "Basic system is working correctly"
        }
        
    except Exception as e:
        logger.error(f"❌ Demo test failed: {str(e)}")
        return {
            "demo_test": "failed",
            "status": "error", 
            "error": str(e),
            "message": "System encountered an error during demo test"
        }

@app.get("/status", tags=["System"])
async def system_status():
    """Get detailed system status"""
    return {
        "platform": "VENDORA Basic",
        "version": "1.5.0",
        "mode": "basic_operation",
        "dependencies": {
            "fastapi": "✅ Available",
            "google_cloud": "❌ Disabled (missing system libs)",
            "basic_analytics": "✅ Available"
        },
        "recommendations": [
            "For cloud features, install system dependencies",
            "Current mode provides basic analytics",
            "Upgrade to cloud mode for BigQuery integration"
        ]
    }

if __name__ == "__main__":
    logger.info("🚀 Starting VENDORA Basic Platform")
    uvicorn.run(
        "working_fastapi_basic:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )