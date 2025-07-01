"""
VENDORA Working FastAPI Application
Enhanced with L1-L2-L3 Agent System Integration
"""

from fastapi import FastAPI, HTTPException, Request, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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

# Enhanced imports for agent integration
from agents.email_processor.mailgun_handler import MailgunWebhookHandler
from agents.data_analyst.enhanced_processor import EnhancedAutomotiveDataProcessor
from agents.conversation_ai.conversation_agent import ConversationAgent

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

# Enhanced Agent System Models
class ConversationRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Natural language query")
    dealer_id: str = Field(..., min_length=1, description="Dealer identifier")
    model: Optional[str] = Field(default=None, description="AI model to use")

class ConversationResponse(BaseModel):
    response: Dict[str, Any]
    model_used: str
    dealer_context: Dict[str, Any] = Field(default_factory=dict)
    insights_count: int = 0
    status: str

class DataAnalysisRequest(BaseModel):
    file_path: str = Field(..., description="Path to CSV file")
    dealer_id: str = Field(..., description="Dealer identifier")

class DataAnalysisResponse(BaseModel):
    status: str
    dataset_type: str
    record_count: int
    insights: Dict[str, Any]
    processed_timestamp: str

class AgentHealthResponse(BaseModel):
    l1_email_processor: str
    l2_data_analyst: str
    l3_conversation_ai: str
    cloud_integration: str
    overall_status: str

# Application state
app.state.initialized = False
app.state.flow_manager = None
app.state.config = {}

# Enhanced Agent System - Global instances
mailgun_handler: Optional[MailgunWebhookHandler] = None
data_processor: Optional[EnhancedAutomotiveDataProcessor] = None
conversation_agent: Optional[ConversationAgent] = None

# Global storage for tasks and metrics
tasks: Dict[str, Dict[str, Any]] = {}
query_metrics = {
    "total_queries": 0,
    "successful_queries": 0,
    "failed_queries": 0,
}

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

# Enhanced Agent System Endpoints

@app.post("/webhook/mailgun")
async def mailgun_webhook(request: Request):
    """L1 Agent: Handle Mailgun webhook for email processing."""
    if not mailgun_handler:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Mailgun handler not initialized"
        )
    
    try:
        # Get raw body and form data
        body = await request.body()
        form_data = await request.form()
        
        # Process webhook
        result = await mailgun_handler.handle_webhook(body, dict(form_data))
        
        if result.get("status") == "success":
            return {"status": "ok", "message": "Email processed successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=result.get("error", "Email processing failed")
            )
            
    except Exception as e:
        logger.error(f"Mailgun webhook error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed"
        )

@app.post("/analyze-data", response_model=DataAnalysisResponse)
async def analyze_data(payload: DataAnalysisRequest):
    """L2 Agent: Analyze CSV data files."""
    if not data_processor:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Data processor not initialized"
        )
    
    try:
        # Process the data file
        result = await data_processor.process_file(
            file_path=payload.file_path,
            dealer_id=payload.dealer_id
        )
        
        return DataAnalysisResponse(
            status="success",
            dataset_type=result.get("dataset_type", "unknown"),
            record_count=result.get("record_count", 0),
            insights=result.get("insights", {}),
            processed_timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Data analysis error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Data analysis failed: {str(e)}"
        )

@app.post("/conversation", response_model=ConversationResponse)
async def conversation_endpoint(payload: ConversationRequest):
    """L3 Agent: Natural language conversation interface."""
    if not conversation_agent:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Conversation agent not initialized"
        )
    
    try:
        # Process the conversation
        result = await conversation_agent.process_query(
            query=payload.query,
            dealer_id=payload.dealer_id,
            model=payload.model
        )
        
        return ConversationResponse(
            response=result.get("response", {}),
            model_used=result.get("model_used", "unknown"),
            dealer_context=result.get("dealer_context", {}),
            insights_count=result.get("insights_count", 0),
            status="success"
        )
        
    except Exception as e:
        logger.error(f"Conversation error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Conversation processing failed: {str(e)}"
        )

@app.get("/agents/health", response_model=AgentHealthResponse)
async def agents_health():
    """Check the health status of all agents."""
    try:
        # Check each agent's status
        l1_status = "healthy" if mailgun_handler else "not_initialized"
        l2_status = "healthy" if data_processor else "not_initialized"
        l3_status = "healthy" if conversation_agent else "not_initialized"
        
        # Check cloud integration
        cloud_status = "healthy" if app.state.initialized else "not_initialized"
        
        # Determine overall status
        all_agents = [l1_status, l2_status, l3_status, cloud_status]
        if all(status == "healthy" for status in all_agents):
            overall_status = "healthy"
        elif any(status == "healthy" for status in all_agents):
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"
        
        return AgentHealthResponse(
            l1_email_processor=l1_status,
            l2_data_analyst=l2_status,
            l3_conversation_ai=l3_status,
            cloud_integration=cloud_status,
            overall_status=overall_status
        )
        
    except Exception as e:
        logger.error(f"Agent health check error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Health check failed"
        )

# Application Lifecycle Events
@app.on_event("startup")
async def startup_event():
    """Handle application startup."""
    global mailgun_handler, data_processor, conversation_agent
    
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
        
        # Initialize Enhanced Agent System
        try:
            # Initialize cloud config first
            from config.cloud_config import CloudConfig
            cloud_config = CloudConfig()
            
            # Initialize L1 Email Processor
            mailgun_handler = MailgunWebhookHandler(cloud_config)
            
            # Initialize L2 Data Analyst
            data_processor = EnhancedAutomotiveDataProcessor(cloud_config)
            
            # Initialize L3 Conversation AI
            conversation_agent = ConversationAgent(cloud_config)
            
            logger.info("✅ Enhanced Agent System initialized successfully")
            logger.info(f"📧 L1 Email Processor: {'✅ Ready' if mailgun_handler else '❌ Failed'}")
            logger.info(f"📊 L2 Data Analyst: {'✅ Ready' if data_processor else '❌ Failed'}")
            logger.info(f"🤖 L3 Conversation AI: {'✅ Ready' if conversation_agent else '❌ Failed'}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize agent system: {str(e)}", exc_info=True)
            # Set agents to None for graceful degradation
            mailgun_handler = None
            data_processor = None
            conversation_agent = None
        
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
