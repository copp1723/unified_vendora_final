from fastapi import FastAPI, HTTPException, Request, Path, Depends, status
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
import logging

# Import security validation
from src.security.input_validator import InputValidator

# Import Firebase authentication
from src.auth.firebase_auth import (
    get_current_user, 
    get_current_verified_user,
    require_dealership_access,
    initialize_firebase_auth,
    get_firebase_auth_handler,
    FirebaseUser,
    RequireRole
)

# Import refined Pydantic models
from src.models.api_models import (
    QueryRequest,
    QueryResponse,
    ErrorResponse,
    ErrorDetail,
    TaskStatusResponse,
    AgentExplanationResponse,
    SystemOverviewResponse,
    SystemMetricsResponse,
    UserInfoResponse,
    CreateUserRequest,
    CreateUserResponse,
    MailgunWebhookResponse,
    QueryMetadata,
    DataVisualization,
    TaskComplexity,
    InsightStatus,
    ConfidenceLevel
)

# Configure logging (can be adopted from existing setup or enhanced)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration for the application
APP_CONFIG = {
    "title": "VENDORA API",
    "description": "VENDORA - Automotive AI Data Platform",
    "version": "1.0.0"
}

# Initialize FastAPI app
app = FastAPI(
    title="VENDORA FastAPI",
    description="VENDORA - Automotive AI Data Platform",
    version="1.0.0",
    # Default responses can be defined globally if needed
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
        504: {"model": ErrorResponse, "description": "Gateway Timeout / Query Processing Timeout"},
        400: {"model": ErrorResponse, "description": "Bad Request"},
        401: {"model": ErrorResponse, "description": "Unauthorized - Invalid or missing authentication"},
        403: {"model": ErrorResponse, "description": "Forbidden - Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Not Found"},
        503: {"model": ErrorResponse, "description": "Service Unavailable"},
    }
)

# MCP functionality temporarily disabled for deployment
# Will be re-enabled once fastapi-mcp package is available

# Placeholder for application state/components
# These will be initialized in the startup event
app.state.initialized = False
app.state.flow_manager = None # Will be instance of HierarchicalFlowManager
app.state.explainability_engine = None # Will be instance of ExplainabilityEngine
app.state.mailgun_handler = None # Will be instance of MailgunHandler
app.state.config = {} # To store loaded configurations (e.g., from .env)

# Input validation using secure validator
def validate_dealership_id(dealership_id: str) -> str:
    """Validate dealership_id format using secure validator."""
    return InputValidator.validate_dealership_id(dealership_id)

def validate_task_id(task_id: str) -> str:
    """Validate task_id format using secure validator."""
    return InputValidator.validate_task_id(task_id)


# --- API Endpoints ---
@app.get("/health", tags=["System"], response_model=Dict[str, Any])
async def health():
    """
    Health check endpoint for the FastAPI application.
    
    Returns system health status and component availability.
    """
    return {
        "status": "healthy" if app.state.initialized else "initializing",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "flow_manager": app.state.flow_manager is not None,
            "explainability_engine": app.state.explainability_engine is not None,
            "firebase_auth": True,  # Always true if endpoint is reached
            "mcp_enabled": False  # Temporarily disabled
        },
        "version": "1.0.0"
    }

@app.post("/api/v1/query", response_model=QueryResponse, tags=["VENDORA API"])
async def process_query(
    payload: QueryRequest, 
    request: Request,
    current_user: FirebaseUser = Depends(get_current_verified_user)
):
    """
    Main endpoint for processing user queries through the hierarchical flow.
    """
    if not app.state.initialized or not app.state.flow_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=ErrorDetail(error="Service unavailable", message="System is not initialized.").dict()
        )

    try:
        validated_dealership_id = validate_dealership_id(payload.dealership_id)
        validated_query = InputValidator.validate_user_query(payload.query)
        validated_context = InputValidator.validate_context_data(payload.context or {})
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"error": "Input validation failed", "message": str(e)})
    
    # Verify user has access to this dealership
    if not current_user.custom_claims.get('admin', False):
        if current_user.dealership_id != validated_dealership_id:
            raise HTTPException(
                status_code=403, 
                detail={"error": "Access denied", "message": f"You don't have access to dealership {validated_dealership_id}"}
            )

    try:
        # Access flow_manager from app.state with validated inputs
        result = await asyncio.wait_for(
            app.state.flow_manager.process_user_query(
                user_query=validated_query,
                dealership_id=validated_dealership_id,
                user_context=validated_context
            ),
            timeout=30.0  # 30 second timeout
        )
        
        # Check if result contains an error
        if "error" in result:
            error_detail = ErrorDetail(
                error=result.get("error", "Processing failed"),
                message=result.get("message"),
                task_id=result.get("task_id"),
                suggestions=result.get("suggestions"),
                quality_score=result.get("quality_score")
            )
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=error_detail.dict(exclude_none=True)
            )
        
        # Transform result to match QueryResponse model
        response = QueryResponse(
            summary=result["summary"],
            detailed_insight=result["detailed_insight"],
            data_visualization=result.get("data_visualization"),
            confidence_level=result["confidence_level"],
            data_sources=result.get("data_sources", []),
            generated_at=result.get("generated_at", datetime.now()),
            metadata=QueryMetadata(**result["metadata"])
        )
        return response

    except asyncio.TimeoutError:
        logger.warning(f"Query processing timed out for dealership: {validated_dealership_id}")
        raise HTTPException(status_code=504, detail={"error": "Query processing timed out", "message": "The analysis is taking longer than expected. Please try a simpler query."})
    except Exception as e:
        logger.error(f"Error processing query for dealership {validated_dealership_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail={"error": "Internal server error", "message": "An unexpected error occurred. Please try again."})

@app.get("/api/v1/task/{task_id}/status", response_model=TaskStatusResponse, tags=["VENDORA API"])
async def get_task_status(
    request: Request,
    task_id: str = Path(..., title="Task ID", description="The ID of the task to get status for, e.g., TASK-12345"),
    current_user: FirebaseUser = Depends(get_current_user)
):
    """
    Get the status of a specific task.
    """
    if not app.state.initialized or not app.state.flow_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=ErrorDetail(error="Service unavailable", message="System is not initialized.").dict()
        )

    try:
        validated_task_id = validate_task_id(task_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"error": "Invalid task ID format", "message": str(e)})

    try:
        status = await app.state.flow_manager.get_flow_status(validated_task_id)

        if status:
            # Transform to TaskStatusResponse
            return TaskStatusResponse(**status)
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=ErrorDetail(error="Task not found", message=f"No task found with ID {task_id}").dict()
            )

    except HTTPException: # Re-raise HTTPExceptions directly
        raise
    except Exception as e:
        logger.error(f"Error getting task status for {task_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail={"error": "Internal server error"})

@app.get("/api/v1/agent/{agent_id}/explanation", response_model=Dict[str, Any], tags=["VENDORA API"])
async def get_agent_explanation(
    request: Request,
    agent_id: str = Path(..., title="Agent ID", description="ID of the agent for explanation (e.g., 'orchestrator')"),
    current_user: FirebaseUser = Depends(get_current_user)
):
    """
    Get detailed explanation of an agent's activities.
    """
    if not app.state.initialized or not app.state.explainability_engine:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail=ErrorDetail(error="Service unavailable", message="Explainability engine is not initialized.").dict()
        )

    valid_agents = ['orchestrator', 'data_analyst', 'senior_analyst', 'master_analyst']
    if agent_id not in valid_agents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=ErrorDetail(
                error="Invalid agent_id", 
                message=f"Valid agents: {', '.join(valid_agents)}"
            ).dict()
        )

    try:
        explanation = app.state.explainability_engine.get_agent_explanation(agent_id)
        # Transform to AgentExplanationResponse
        return AgentExplanationResponse(**explanation)
    except Exception as e:
        logger.error(f"Error getting agent explanation for {agent_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=ErrorDetail(error="Internal server error").dict()
        )

@app.get("/api/v1/system/overview", response_model=Dict[str, Any], tags=["VENDORA API"])
async def get_system_overview(
    request: Request,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """
    Get system-wide overview.
    """
    if not app.state.initialized or not app.state.explainability_engine:
        raise HTTPException(status_code=503, detail={"error": "Service unavailable", "message": "Explainability engine is not initialized."})

    try:
        overview = app.state.explainability_engine.get_system_overview()
        # Transform to SystemOverviewResponse
        return SystemOverviewResponse(**overview)
    except Exception as e:
        logger.error(f"Error getting system overview: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=ErrorDetail(error="Internal server error").dict()
        )

@app.get("/api/v1/system/metrics", response_model=Dict[str, Any], tags=["VENDORA API"])
async def get_system_metrics(
    request: Request,
    current_user: FirebaseUser = Depends(RequireRole(["admin", "analyst"]))
):
    """
    Get system metrics.
    """
    if not app.state.initialized or not app.state.flow_manager:
        raise HTTPException(status_code=503, detail={"error": "Service unavailable", "message": "Flow manager is not initialized."})

    try:
        flow_metrics = await app.state.flow_manager.get_metrics()
        return SystemMetricsResponse(
            flow_metrics=flow_metrics,
            timestamp=datetime.now()
        )
    except Exception as e:
        logger.error(f"Error getting system metrics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=ErrorDetail(error="Internal server error").dict()
        )

# --- Authentication Endpoints ---

@app.get("/api/v1/auth/me", response_model=UserInfoResponse, tags=["Authentication"])
async def get_current_user_info(
    current_user: FirebaseUser = Depends(get_current_user)
):
    """
    Get current authenticated user information.
    
    This endpoint returns the user's profile information based on their
    Firebase authentication token.
    """
    return UserInfoResponse(
        uid=current_user.uid,
        email=current_user.email,
        email_verified=current_user.email_verified,
        display_name=current_user.display_name,
        dealership_id=current_user.dealership_id,
        roles=current_user.custom_claims.get('roles', []),
        is_admin=current_user.custom_claims.get('admin', False)
    )

@app.post("/api/v1/auth/users", response_model=CreateUserResponse, tags=["Authentication"], include_in_schema=False)
async def create_user(
    user_data: CreateUserRequest,
    current_user: FirebaseUser = Depends(RequireRole(["admin"]))
):
    """
    Create a new user (Admin only).
    
    This endpoint is typically not exposed in production and should be
    handled through Firebase Console or Admin SDK directly.
    """
    auth_handler = get_firebase_auth_handler()
    result = await auth_handler.create_user(
        email=user_data.email,
        password=user_data.password,
        display_name=user_data.display_name,
        dealership_id=user_data.dealership_id
    )
    return result

@app.post("/api/v1/webhook/mailgun", status_code=200, tags=["Webhooks"])
async def mailgun_webhook(request: Request):
    """
    Handle incoming emails from Mailgun.
    FastAPI's `request.form()` will handle parsing of `multipart/form-data` or `application/x-www-form-urlencoded`.
    The MailgunHandler will need to be adapted if it expects a Flask request object directly.
    For now, we pass the FastAPI request object.
    """
    if not app.state.initialized or not app.state.mailgun_handler or not app.state.flow_manager:
        logger.error("Mailgun webhook called but system not fully initialized (mailgun_handler or flow_manager missing).")
        raise HTTPException(status_code=503, detail={"error": "Service unavailable", "message": "System is not fully initialized to handle emails."})

    try:
        # The MailgunHandler.process_webhook might need adjustment
        # if it directly accesses Flask-specific request attributes.
        # Ideally, it should work with data extracted from the request.
        # For now, passing the FastAPI request object.
        # If MailgunHandler expects a Flask request, this will need a shim or refactor of MailgunHandler.

        # mailgun_handler.process_webhook in Flask took `request` (Flask request)
        # We need to see if it can take `await request.form()` or the FastAPI `request` object directly
        # For now, let's assume it might need the form data.
        # Actual implementation of MailgunHandler will determine the exact needs.

        # Placeholder: The original Flask code passed the entire request object.
        # We need to ensure MailgunHandler can work with FastAPI's Request or its parts.
        # This might require refactoring MailgunHandler.
        # For a first pass, let's assume MailgunHandler's process_webhook
        # can be adapted or already works with a dictionary-like form data.

        # The original `self.mailgun_handler.process_webhook(request)`
        # needs to be compatible. If it requires Flask's request,
        # we'll need to adapt it or pass data like `await request.form()`.
        # For this step, we'll call it as is, assuming it will be adapted in MailgunHandler.

        result = await app.state.mailgun_handler.process_webhook(request) # This line is the critical one for compatibility

        if result.get('contains_query'):
            logger.info(f"Mailgun webhook: processing extracted query for dealership {result['dealership_id']}")
            query_result = await app.state.flow_manager.process_user_query(
                user_query=result['extracted_query'],
                dealership_id=result['dealership_id'],
                user_context={
                    "source": "email",
                    "sender": result['sender']
                }
            )

            # Send response via email
            await app.state.mailgun_handler.send_insight_email(
                to=result['sender'],
                insight=query_result # Ensure this is the data structure send_insight_email expects
            )
            logger.info(f"Mailgun webhook: Insight email sent to {result['sender']}")

        return MailgunWebhookResponse(status="processed", message="Email processed successfully")

    except Exception as e:
        logger.error(f"Error processing mailgun webhook: {str(e)}", exc_info=True)
        # Return a 200 as per Mailgun's recommendation to avoid retries for application errors,
        # but log the error thoroughly. Or choose a 500 if preferred.
        # The original Flask app returned 500. Let's stick to that for now.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=ErrorDetail(error="Webhook processing failed", message=str(e)).dict()
        )

import os
from dotenv import load_dotenv

# Import services needed for initialization
# These paths might need adjustment based on your project structure
from services.hierarchical_flow_manager import HierarchicalFlowManager
from services.explainability_engine import ExplainabilityEngine
from agents.email_processor.mailgun_handler import MailgunHandler

# --- Application Lifecycle Events (Startup and Shutdown) ---

@app.on_event("startup")
async def startup_event():
    """
    Handles application startup:
    - Loads configuration.
    - Initializes services (FlowManager, ExplainabilityEngine, MailgunHandler).
    - Sets application state.
    """
    logger.info("🚀 Initializing VENDORA FastAPI Platform...")

    # Load environment variables
    load_dotenv()

    # Configuration loading (similar to original main.py and VendoraApp.__init__)
    # This config will be stored in app.state.config and used by services
    app_config = {
        'OPENROUTER_API_KEY': os.getenv('OPENROUTER_API_KEY'), # Used by OpenRouter client if ConversationAgent uses it
        'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY'), # Used by HierarchicalFlowManager
        'BIGQUERY_PROJECT': os.getenv('BIGQUERY_PROJECT', 'vendora-analytics'), # Used by HierarchicalFlowManager
        'MAILGUN_PRIVATE_API_KEY': os.getenv('MAILGUN_PRIVATE_API_KEY'), # Used by MailgunHandler
        'MAILGUN_DOMAIN': os.getenv('MAILGUN_DOMAIN'), # Used by MailgunHandler
        'FIREBASE_PROJECT_ID': os.getenv('FIREBASE_PROJECT_ID', 'vendora-analytics'), # Firebase project ID
        'FIREBASE_SERVICE_ACCOUNT_PATH': os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH'), # Optional service account
        'MAILGUN_SENDING_API_KEY': os.getenv('MAILGUN_SENDING_API_KEY'), # Used by MailgunHandler for sending
        'SUPERMEMORY_API_KEY': os.getenv('SUPERMEMORY_API_KEY'), # Used by SuperMemory client if ConversationAgent uses it
        'DATA_STORAGE_PATH': os.getenv('DATA_STORAGE_PATH', './data'),
        'MEMORY_STORAGE_PATH': os.getenv('MEMORY_STORAGE_PATH', './memory'),
        'QUALITY_THRESHOLD': os.getenv('QUALITY_THRESHOLD', '0.85'), # Used by HierarchicalFlowManager
        'GOOGLE_APPLICATION_CREDENTIALS': os.getenv('GOOGLE_APPLICATION_CREDENTIALS') # Used by HierarchicalFlowManager
    }
    app.state.config = app_config

    # Validate required configuration (example for GEMINI_API_KEY)
    # Add other critical keys as necessary
    required_keys_startup = ['GEMINI_API_KEY']
    missing_keys = [key for key in required_keys_startup if not app_config.get(key)]
    if missing_keys:
        logger.error(f"❌ Missing required configuration for startup: {missing_keys}. Check .env file.")
        # Decide if the app should fail to start or run in a degraded mode
        # For now, we'll log and continue, but services might fail.
        # Consider raising an exception here to prevent startup if critical configs are missing.
        # raise RuntimeError(f"Missing critical configuration: {missing_keys}")
        # For now, let's proceed but mark as not fully initialized.
        app.state.initialized = False
        logger.warning("Continuing startup with missing critical configuration. Some services may not function.")
        # Do not proceed with initializing components that depend on missing keys
        return

    try:
        # Initialize Firebase Authentication
        try:
            initialize_firebase_auth(app_config)
            logger.info("✅ Firebase Authentication initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase Auth: {e}")
            # Continue without auth in development mode
            if os.getenv('ENVIRONMENT') != 'development':
                raise
        
        # Initialize hierarchical flow manager
        flow_config_params = {
            "gemini_api_key": app_config.get('GEMINI_API_KEY'),
            "bigquery_project": app_config.get('BIGQUERY_PROJECT'),
            "quality_threshold": float(app_config.get('QUALITY_THRESHOLD', 0.85)),
            "service_account_path": app_config.get('GOOGLE_APPLICATION_CREDENTIALS')
        }
        if flow_config_params["gemini_api_key"]: # Only init if key is present
            app.state.flow_manager = HierarchicalFlowManager(flow_config_params)
            await app.state.flow_manager.initialize()
            logger.info("✅ HierarchicalFlowManager initialized.")
        else:
            logger.warning("GEMINI_API_KEY not found. HierarchicalFlowManager not initialized.")

        # Initialize explainability engine
        app.state.explainability_engine = ExplainabilityEngine()
        await app.state.explainability_engine.start() # Assuming ExplainabilityEngine has an async start
        logger.info("✅ ExplainabilityEngine initialized and started.")

        # Initialize Mailgun handler if configured
        if app_config.get('MAILGUN_PRIVATE_API_KEY') and app_config.get('MAILGUN_DOMAIN'):
            # MailgunHandler in Flask app took the whole config dict.
            # Ensure it can still do so or adapt it.
            app.state.mailgun_handler = MailgunHandler(app_config)
            logger.info("✅ MailgunHandler initialized.")
        else:
            logger.warning("Mailgun API key or domain not configured. MailgunHandler not initialized.")

        app.state.initialized = True # Set to True if all critical initializations succeeded
        logger.info("✅ VENDORA FastAPI Platform initialized successfully.")

    except Exception as e:
        logger.error(f"❌ Failed to initialize platform components: {str(e)}", exc_info=True)
        app.state.initialized = False # Ensure it's marked as not initialized on failure
        # Depending on severity, you might want to raise the exception
        # to prevent the app from starting in a broken state.
        # raise e

@app.on_event("shutdown")
async def shutdown_event():
    """
    Handles application shutdown:
    - Gracefully shuts down services.
    """
    logger.info("🛑 Shutting down VENDORA FastAPI Platform...")
    try:
        if hasattr(app.state, 'flow_manager') and app.state.flow_manager:
            await app.state.flow_manager.shutdown()
            logger.info("✅ HierarchicalFlowManager shutdown.")

        if hasattr(app.state, 'explainability_engine') and app.state.explainability_engine:
            await app.state.explainability_engine.stop() # Assuming an async stop
            logger.info("✅ ExplainabilityEngine stopped.")

        # Add shutdown for MailgunHandler if it has any state to clean up (e.g., client sessions)
        # if hasattr(app.state, 'mailgun_handler') and app.state.mailgun_handler:
        #     await app.state.mailgun_handler.shutdown() # If it had an async shutdown
        #     logger.info("✅ MailgunHandler shutdown.")

        logger.info("✅ VENDORA FastAPI Platform shutdown complete.")
    except Exception as e:
        logger.error(f"Error during platform shutdown: {str(e)}", exc_info=True)

if __name__ == "__main__":
    import uvicorn
    # This is for local development/testing of this file directly.
    # The main entry point will be src/main.py using uvicorn programmatically or via CLI.
    # Note: load_dotenv() is called in startup_event. If running this directly
    # and .env is needed before startup_event (e.g. for Uvicorn config itself),
    # it might need to be called earlier here too.
    uvicorn.run("fastapi_main:app", host="0.0.0.0", port=8000, reload=True)
