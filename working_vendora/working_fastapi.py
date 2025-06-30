"""
VENDORA Working FastAPI Application
A clean, functional version that actually works
"""

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
import logging
import re
import uuid
import os
from dotenv import load_dotenv

# Import our working flow manager
from minimal_flow_manager import MinimalFlowManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="VENDORA API",
    description="VENDORA - Automotive AI Data Platform (Working Version)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User query to process")
    dealership_id: str = Field(..., min_length=1, description="Dealership identifier")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")

class QueryResponse(BaseModel):
    summary: str
    detailed_insight: Dict[str, Any]
    confidence_level: str
    data_sources: List[str] = Field(default_factory=list)
    generated_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    complexity: str
    created_at: str
    query: str

class SystemMetrics(BaseModel):
    total_queries: int
    successful_queries: int
    failed_queries: int
    active_tasks: int
    total_tasks: int
    success_rate: float

class ErrorResponse(BaseModel):
    error: str
    message: Optional[str] = None
    task_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

# Application state
app.state.initialized = False
app.state.flow_manager = None
app.state.config = {}

# Utility functions
def is_valid_dealership_id(dealership_id: str) -> bool:
    """Validate dealership_id format."""
    return bool(re.fullmatch(r"^[a-zA-Z0-9_-]+$", dealership_id))

def validate_query(query: str) -> bool:
    """Validate query content."""
    return len(query.strip()) >= 3 and len(query) <= 1000

# API Endpoints
@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy" if app.state.initialized else "initializing",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "service": "vendora-api"
    }

@app.post("/api/v1/query", response_model=QueryResponse)
async def process_query(payload: QueryRequest):
    """
    Main endpoint for processing user queries through the hierarchical flow.
    """
    
    # Validation
    if not app.state.initialized or not app.state.flow_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service is not initialized"
        )
    
    if not is_valid_dealership_id(payload.dealership_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid dealership_id format"
        )
    
    if not validate_query(payload.query):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query must be between 3 and 1000 characters"
        )
    
    try:
        # Process the query
        result = await asyncio.wait_for(
            app.state.flow_manager.process_user_query(
                user_query=payload.query,
                dealership_id=payload.dealership_id,
                user_context=payload.context
            ),
            timeout=30.0
        )
        
        # Check for errors in result
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=result
            )
        
        # Return successful response
        return QueryResponse(**result)
        
    except asyncio.TimeoutError:
        logger.warning(f"Query processing timed out for dealership: {payload.dealership_id}")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail={
                "error": "Query processing timed out",
                "message": "The analysis is taking longer than expected. Please try a simpler query."
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing query for dealership {payload.dealership_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "message": "An unexpected error occurred. Please try again."
            }
        )

@app.get("/api/v1/task/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """Get the status of a specific task."""
    
    if not app.state.initialized or not app.state.flow_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service is not initialized"
        )
    
    if not task_id.startswith('TASK-'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid task ID format"
        )
    
    try:
        status_info = await app.state.flow_manager.get_flow_status(task_id)
        
        if not status_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )
        
        return TaskStatusResponse(**status_info)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task status for {task_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving task status"
        )

@app.get("/api/v1/system/metrics", response_model=SystemMetrics)
async def get_system_metrics():
    """Get system metrics."""
    
    if not app.state.initialized or not app.state.flow_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service is not initialized"
        )
    
    try:
        metrics = await app.state.flow_manager.get_metrics()
        return SystemMetrics(**metrics)
        
    except Exception as e:
        logger.error(f"Error getting system metrics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving system metrics"
        )

@app.get("/api/v1/system/status")
async def get_system_status():
    """Get detailed system status."""
    
    flow_manager_status = "healthy" if app.state.flow_manager else "not_initialized"
    
    return {
        "overall_status": "healthy" if app.state.initialized else "initializing",
        "components": {
            "flow_manager": flow_manager_status,
            "gemini_api": "configured" if app.state.config.get('GEMINI_API_KEY') else "not_configured"
        },
        "config": {
            "gemini_configured": bool(app.state.config.get('GEMINI_API_KEY')),
            "bigquery_project": app.state.config.get('BIGQUERY_PROJECT', 'not_set'),
            "quality_threshold": app.state.config.get('QUALITY_THRESHOLD', 0.85)
        },
        "timestamp": datetime.now().isoformat()
    }

# Application Lifecycle Events
@app.on_event("startup")
async def startup_event():
    """Handle application startup."""
    logger.info("🚀 Starting VENDORA FastAPI Platform...")
    
    try:
        # Load environment variables
        load_dotenv()
        
        # Configuration
        app.state.config = {
            'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY'),
            'BIGQUERY_PROJECT': os.getenv('BIGQUERY_PROJECT', 'vendora-analytics'),
            'QUALITY_THRESHOLD': float(os.getenv('QUALITY_THRESHOLD', '0.85')),
            'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO')
        }
        
        # Initialize Flow Manager
        app.state.flow_manager = MinimalFlowManager(app.state.config)
        await app.state.flow_manager.initialize()
        
        app.state.initialized = True
        
        logger.info("✅ VENDORA Platform initialized successfully")
        logger.info(f"📊 Gemini API: {'✅ Configured' if app.state.config.get('GEMINI_API_KEY') else '❌ Not configured'}")
        logger.info(f"📊 BigQuery Project: {app.state.config.get('BIGQUERY_PROJECT')}")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize platform: {str(e)}", exc_info=True)
        app.state.initialized = False
        # Don't raise exception - let app start in degraded mode

@app.on_event("shutdown")
async def shutdown_event():
    """Handle application shutdown."""
    logger.info("🛑 Shutting down VENDORA Platform...")
    
    try:
        if app.state.flow_manager:
            await app.state.flow_manager.shutdown()
        
        logger.info("✅ VENDORA Platform shutdown complete")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}", exc_info=True)

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler."""
    return {
        "error": "HTTP Exception",
        "status_code": exc.status_code,
        "detail": exc.detail,
        "timestamp": datetime.now().isoformat()
    }

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return {
        "error": "Internal Server Error",
        "message": "An unexpected error occurred",
        "timestamp": datetime.now().isoformat()
    }

# Development server
if __name__ == "__main__":
    import uvicorn
    
    # Load environment for development
    load_dotenv()
    
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 8000))
    log_level = os.getenv('LOG_LEVEL', 'info').lower()
    reload = os.getenv('RELOAD', 'True').lower() == 'true'
    
    logger.info(f"🚀 Starting VENDORA development server on {host}:{port}")
    
    uvicorn.run(
        "working_fastapi:app",
        host=host,
        port=port,
        log_level=log_level,
        reload=reload
    )
