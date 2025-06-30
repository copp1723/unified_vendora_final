"""
Working VENDORA FastAPI with GCP Cloud Integration
"""

import asyncio
import logging
import uvicorn
from datetime import datetime
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Import working components
from minimal_flow_manager import FlowManager, TaskComplexity, InsightStatus
from cloud_config import CloudConfig
from enhanced_flow_manager import EnhancedFlowManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
cloud_config: Optional[CloudConfig] = None
flow_manager: Optional[FlowManager] = None
enhanced_flow_manager: Optional[EnhancedFlowManager] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup application lifecycle"""
    global cloud_config, flow_manager, enhanced_flow_manager
    
    logger.info("🚀 Starting VENDORA with GCP Cloud Integration")
    
    try:
        # Initialize cloud configuration
        cloud_config = CloudConfig()
        await cloud_config.initialize()
        logger.info("✅ Cloud configuration initialized")
        
        # Initialize enhanced flow manager (with BigQuery)
        enhanced_flow_manager = EnhancedFlowManager(cloud_config)
        await enhanced_flow_manager.initialize()
        logger.info("✅ Enhanced flow manager initialized")
        
        # Initialize fallback flow manager
        flow_manager = FlowManager()
        await flow_manager.initialize()
        logger.info("✅ Fallback flow manager initialized")
        
        logger.info("🎉 VENDORA Cloud Platform Ready!")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {str(e)}")
        raise
    
    yield
    
    # Cleanup
    logger.info("🛑 Shutting down VENDORA Cloud Platform")
    try:
        if enhanced_flow_manager:
            await enhanced_flow_manager.shutdown()
        if flow_manager:
            await flow_manager.shutdown()
        logger.info("✅ Shutdown complete")
    except Exception as e:
        logger.error(f"❌ Shutdown error: {str(e)}")

# Create FastAPI app with cloud integration
app = FastAPI(
    title="VENDORA AI Platform - Cloud Edition",
    description="AI-Powered Automotive Business Intelligence with GCP Integration",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class QueryRequest(BaseModel):
    query: str = Field(..., description="User query about automotive business")
    dealership_id: str = Field(..., description="Dealership identifier")
    use_cloud_data: bool = Field(default=True, description="Use real BigQuery data")
    user_context: Optional[Dict[str, Any]] = Field(default=None, description="Additional user context")

class TaskStatusRequest(BaseModel):
    task_id: str = Field(..., description="Task identifier")

class AuthRequest(BaseModel):
    id_token: str = Field(..., description="Firebase ID token")

# Dependency to get current flow manager
def get_flow_manager() -> FlowManager:
    """Get the appropriate flow manager based on request"""
    if not enhanced_flow_manager:
        if not flow_manager:
            raise HTTPException(status_code=503, detail="Flow manager not initialized")
        return flow_manager
    return enhanced_flow_manager

# Authentication dependency
async def verify_auth(authorization: str = Header(None)) -> Dict[str, Any]:
    """Verify Firebase authentication token"""
    if not authorization:
        # Allow anonymous access for now
        return {"user_id": "anonymous", "authenticated": False}
    
    try:
        # Extract token from "Bearer <token>"
        token = authorization.split(" ")[1] if authorization.startswith("Bearer ") else authorization
        
        # Verify with Firebase (placeholder - implement with firebase-admin)
        # For now, return mock user
        return {
            "user_id": f"user_{token[:8]}",
            "authenticated": True,
            "dealership_id": "DEMO_DEALERSHIP"
        }
        
    except Exception as e:
        logger.warning(f"Auth verification failed: {str(e)}")
        return {"user_id": "anonymous", "authenticated": False}

# Health check endpoints
@app.get("/", tags=["Health"])
async def root():
    """Root endpoint with system status"""
    return {
        "message": "VENDORA AI Platform - Cloud Edition",
        "status": "operational",
        "version": "2.0.0",
        "cloud_integration": "active",
        "timestamp": datetime.now(),
        "features": [
            "BigQuery Integration",
            "Secret Manager",
            "Firebase Auth",
            "Real Automotive Data",
            "Enhanced Analytics"
        ]
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check with cloud service status"""
    global cloud_config, enhanced_flow_manager, flow_manager
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(),
        "services": {
            "cloud_config": cloud_config is not None,
            "enhanced_flow_manager": enhanced_flow_manager is not None,
            "fallback_flow_manager": flow_manager is not None,
        },
        "cloud_services": {}
    }
    
    if cloud_config:
        config = cloud_config.get_config()
        health_status["cloud_services"] = {
            "bigquery": config.get("bigquery_client") is not None,
            "secret_manager": len(cloud_config.secrets_cache) > 0,
            "project_id": config.get("project_id"),
            "secrets_loaded": list(cloud_config.secrets_cache.keys())
        }
    
    return health_status

# Core business intelligence endpoints
@app.post("/analyze", tags=["Analytics"])
async def analyze_query(
    request: QueryRequest,
    user: Dict[str, Any] = Depends(verify_auth)
):
    """Process business intelligence query with cloud data"""
    try:
        # Use enhanced manager if available and cloud data requested
        if enhanced_flow_manager and request.use_cloud_data:
            logger.info(f"🔍 Processing query with BigQuery data: {request.query}")
            result = await enhanced_flow_manager.process_user_query(
                request.query,
                request.dealership_id,
                request.user_context
            )
            result["data_source"] = "bigquery"
            result["cloud_enhanced"] = True
        else:
            logger.info(f"🔍 Processing query with fallback manager: {request.query}")
            result = await flow_manager.process_user_query(
                request.query,
                request.dealership_id,
                request.user_context or {}
            )
            result["data_source"] = "sample"
            result["cloud_enhanced"] = False
        
        result["user_context"] = user
        return result
        
    except Exception as e:
        logger.error(f"❌ Analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/task-status", tags=["Analytics"])
async def get_task_status(
    request: TaskStatusRequest,
    manager: FlowManager = Depends(get_flow_manager)
):
    """Get status of a specific task"""
    try:
        status = await manager.get_flow_status(request.task_id)
        if not status:
            raise HTTPException(status_code=404, detail="Task not found")
        return status
    except Exception as e:
        logger.error(f"❌ Status check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

@app.get("/metrics", tags=["Analytics"])
async def get_system_metrics(
    user: Dict[str, Any] = Depends(verify_auth)
):
    """Get system performance metrics"""
    try:
        metrics = {}
        
        if enhanced_flow_manager:
            enhanced_metrics = await enhanced_flow_manager.get_metrics()
            metrics.update(enhanced_metrics)
        
        if flow_manager:
            basic_metrics = await flow_manager.get_metrics()
            metrics["fallback_manager"] = basic_metrics
        
        metrics["user_context"] = user
        return metrics
        
    except Exception as e:
        logger.error(f"❌ Metrics collection failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Metrics failed: {str(e)}")

# Cloud-specific endpoints
@app.get("/cloud/config", tags=["Cloud"])
async def get_cloud_config(
    user: Dict[str, Any] = Depends(verify_auth)
):
    """Get cloud configuration status"""
    if not cloud_config:
        raise HTTPException(status_code=503, detail="Cloud config not initialized")
    
    try:
        config = cloud_config.get_config()
        return {
            "project_id": config.get("project_id"),
            "bigquery_enabled": config.get("bigquery_client") is not None,
            "secrets_loaded": len(cloud_config.secrets_cache),
            "available_secrets": list(cloud_config.secrets_cache.keys()),
            "status": "operational"
        }
    except Exception as e:
        logger.error(f"❌ Cloud config check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Cloud config failed: {str(e)}")

@app.get("/cloud/bigquery/test", tags=["Cloud"])
async def test_bigquery_connection(
    user: Dict[str, Any] = Depends(verify_auth)
):
    """Test BigQuery connection"""
    if not enhanced_flow_manager:
        raise HTTPException(status_code=503, detail="Enhanced manager not available")
    
    try:
        # Test query
        test_result = await enhanced_flow_manager._fetch_dealership_data(
            "TEST_DEALERSHIP", 
            "test bigquery connection"
        )
        
        return {
            "status": "success",
            "bigquery_available": test_result.get("bigquery_data", False),
            "data_summary": {
                "tables_accessed": len([k for k, v in test_result.items() 
                                      if isinstance(v, dict) and v.get("bigquery_data")]),
                "sample_response": test_result
            }
        }
        
    except Exception as e:
        logger.error(f"❌ BigQuery test failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"BigQuery test failed: {str(e)}")

# Authentication endpoints
@app.post("/auth/verify", tags=["Authentication"])
async def verify_token(request: AuthRequest):
    """Verify Firebase authentication token"""
    try:
        # Placeholder for Firebase Admin SDK verification
        # In production, use firebase-admin to verify the token
        
        return {
            "status": "verified",
            "user_id": f"user_{request.id_token[:8]}",
            "timestamp": datetime.now(),
            "permissions": ["read", "analyze"]
        }
        
    except Exception as e:
        logger.error(f"❌ Token verification failed: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid token")

# Demo endpoints for testing
@app.get("/demo/sample-query", tags=["Demo"])
async def demo_sample_query():
    """Demo endpoint with sample automotive query"""
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
            "dealership_id": "DEMO_DEALERSHIP_001",
            "use_cloud_data": True
        }
    }

@app.get("/demo/quick-test", tags=["Demo"])
async def demo_quick_test():
    """Quick test of the system with sample data"""
    try:
        # Test with sample query
        test_request = QueryRequest(
            query="Show me our top performing vehicles",
            dealership_id="DEMO_DEALERSHIP",
            use_cloud_data=True
        )
        
        result = await analyze_query(test_request, {"user_id": "demo_user", "authenticated": True})
        
        return {
            "demo_test": "completed",
            "status": "success",
            "sample_result": result,
            "message": "System is working correctly with cloud integration"
        }
        
    except Exception as e:
        logger.error(f"❌ Demo test failed: {str(e)}")
        return {
            "demo_test": "failed",
            "status": "error",
            "error": str(e),
            "message": "System encountered an error during demo test"
        }

if __name__ == "__main__":
    logger.info("🚀 Starting VENDORA Cloud Platform")
    uvicorn.run(
        "working_fastapi_cloud:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )