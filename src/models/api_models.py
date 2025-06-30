"""
Pydantic Models for VENDORA FastAPI Application
Defines request and response models for all API endpoints
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator
from src.security.input_validator import InputValidator


# Enums
class TaskComplexity(str, Enum):
    """Task complexity levels"""
    SIMPLE = "simple"
    STANDARD = "standard"
    COMPLEX = "complex"
    CRITICAL = "critical"


class InsightStatus(str, Enum):
    """Insight generation status"""
    PENDING = "pending"
    ANALYZING = "analyzing"
    GENERATING = "generating"
    VALIDATING = "validating"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION_NEEDED = "revision_needed"
    DELIVERED = "delivered"


class ConfidenceLevel(str, Enum):
    """Confidence levels for insights"""
    VERY_HIGH = "Very High"
    HIGH = "High"
    MODERATE = "Moderate"
    LOW = "Low"
    VERY_LOW = "Very Low"


class VisualizationType(str, Enum):
    """Supported visualization types"""
    LINE_CHART = "line_chart"
    BAR_CHART = "bar_chart"
    PIE_CHART = "pie_chart"
    TABLE = "table"
    HEATMAP = "heatmap"
    SCATTER_PLOT = "scatter_plot"


class AgentPhase(str, Enum):
    """Agent execution phases"""
    INITIALIZING = "initializing"
    PLANNING = "planning"
    ANALYZING = "analyzing"
    IMPLEMENTING = "implementing"
    TESTING = "testing"
    REVIEWING = "reviewing"
    COMPLETING = "completing"
    FAILED = "failed"


# Request Models
class QueryRequest(BaseModel):
    """Request model for processing analytical queries"""
    query: str = Field(..., description="The analytical query to process", min_length=1, max_length=1000)
    dealership_id: str = Field(..., description="Dealership identifier", pattern="^[a-zA-Z0-9_-]+$")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context for the query")
    
    @validator('query')
    def validate_query(cls, v):
        return InputValidator.validate_user_query(v)
    
    @validator('dealership_id')
    def validate_dealership_id(cls, v):
        return InputValidator.validate_dealership_id(v)
    
    @validator('context')
    def validate_context(cls, v):
        return InputValidator.validate_context_data(v or {})
    
    class Config:
        schema_extra = {
            "example": {
                "query": "What were my top selling vehicles last month?",
                "dealership_id": "dealer_123",
                "context": {
                    "user_role": "sales_manager",
                    "preferences": {"format": "detailed"}
                }
            }
        }


# Response Models
class DataVisualization(BaseModel):
    """Data visualization configuration"""
    type: VisualizationType
    config: Dict[str, Any] = Field(..., description="Chart-specific configuration")
    
    class Config:
        use_enum_values = True


class QueryMetadata(BaseModel):
    """Metadata for query processing"""
    task_id: str = Field(..., description="Unique task identifier", pattern="^TASK-[a-f0-9]{8}$")
    complexity: TaskComplexity
    processing_time_ms: int = Field(..., ge=0, description="Total processing time in milliseconds")
    revision_count: int = Field(0, ge=0, description="Number of revisions")
    cached: bool = Field(False, description="Whether result was from cache")
    
    class Config:
        use_enum_values = True


class QueryResponse(BaseModel):
    """Response model for successful query processing"""
    summary: str = Field(..., description="Natural language summary of the insight")
    detailed_insight: Dict[str, Any] = Field(..., description="Detailed analytical insights")
    data_visualization: Optional[DataVisualization] = Field(None, description="Visualization configuration")
    confidence_level: ConfidenceLevel = Field(..., description="Confidence level of the insight")
    data_sources: List[str] = Field(default_factory=list, description="Data sources used")
    generated_at: datetime = Field(..., description="Timestamp of generation")
    metadata: QueryMetadata = Field(..., description="Processing metadata")
    
    class Config:
        use_enum_values = True
        schema_extra = {
            "example": {
                "summary": "Your top selling vehicles last month were F-150, Silverado, and RAV4",
                "detailed_insight": {
                    "top_vehicles": [
                        {"model": "F-150", "units_sold": 45, "revenue": 2250000},
                        {"model": "Silverado", "units_sold": 38, "revenue": 1900000},
                        {"model": "RAV4", "units_sold": 32, "revenue": 1120000}
                    ],
                    "total_sales": 285,
                    "month_over_month_change": "+12.5%"
                },
                "data_visualization": {
                    "type": "bar_chart",
                    "config": {
                        "x_axis": "vehicle_model",
                        "y_axis": "units_sold",
                        "title": "Top Selling Vehicles - Last Month"
                    }
                },
                "confidence_level": "High",
                "data_sources": ["sales_transactions", "inventory"],
                "generated_at": "2024-01-15T10:30:00Z",
                "metadata": {
                    "task_id": "TASK-1a2b3c4d",
                    "complexity": "standard",
                    "processing_time_ms": 1250,
                    "revision_count": 0,
                    "cached": False
                }
            }
        }


class ErrorDetail(BaseModel):
    """Detailed error information"""
    error: str = Field(..., description="Error type or code")
    message: Optional[str] = Field(None, description="Detailed error message")
    task_id: Optional[str] = Field(None, description="Associated task ID")
    suggestions: Optional[List[str]] = Field(None, description="Suggestions for resolution")
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Quality score if available")


class ErrorResponse(BaseModel):
    """Standard error response"""
    detail: Union[str, ErrorDetail] = Field(..., description="Error details")
    
    class Config:
        schema_extra = {
            "example": {
                "detail": {
                    "error": "Invalid dealership_id format",
                    "message": "Dealership ID must contain only alphanumeric characters, hyphens, and underscores"
                }
            }
        }


class FlowError(BaseModel):
    """Error details in flow status"""
    timestamp: datetime
    error_type: str
    message: str
    details: Optional[Dict[str, Any]] = None


class TaskStatusResponse(BaseModel):
    """Response model for task status queries"""
    task_id: str = Field(..., pattern="^TASK-[a-f0-9]{8}$")
    status: InsightStatus
    current_level: int = Field(..., ge=1, le=3, description="Current hierarchy level")
    complexity: TaskComplexity
    duration_ms: int = Field(..., ge=0, description="Total duration in milliseconds")
    draft_insights_count: int = Field(0, ge=0)
    has_validated_insight: bool = False
    error_count: int = Field(0, ge=0)
    errors: List[FlowError] = Field(default_factory=list, description="Last 3 errors")
    
    class Config:
        use_enum_values = True


# Agent Explanation Models
class OperationSummary(BaseModel):
    """Summary of agent operations"""
    total: int = Field(..., ge=0)
    by_type: Dict[str, int] = Field(default_factory=dict)
    success_rate: float = Field(..., ge=0.0, le=1.0)
    total_duration_ms: int = Field(..., ge=0)
    avg_duration_ms: float = Field(..., ge=0.0)
    slow_operations: int = Field(0, ge=0)
    recent_operations: List[Dict[str, Any]] = Field(default_factory=list, max_items=10)


class AgentSummary(BaseModel):
    """Agent activity summary"""
    agent_id: str
    phase: AgentPhase
    current_task: Optional[str] = None
    duration_seconds: float = Field(..., ge=0.0)
    operations_count: int = Field(0, ge=0)
    files_accessed: int = Field(0, ge=0)
    errors_count: int = Field(0, ge=0)
    success_rate: float = Field(1.0, ge=0.0, le=1.0)
    
    class Config:
        use_enum_values = True


class AgentExplanationResponse(BaseModel):
    """Response model for agent explanations"""
    agent_id: str
    current_phase: AgentPhase
    current_task: Optional[str] = None
    duration: str = Field(..., description="Human-readable duration")
    summary: AgentSummary
    operations: OperationSummary
    files_modified: List[str] = Field(default_factory=list)
    decisions: List[Dict[str, Any]] = Field(default_factory=list, max_items=5)
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    timeline: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    
    class Config:
        use_enum_values = True


# System Overview Models
class SystemOverviewResponse(BaseModel):
    """Response model for system overview"""
    timestamp: datetime
    active_agents: int = Field(..., ge=0)
    total_agents: int = Field(..., ge=0)
    total_operations: int = Field(..., ge=0)
    total_errors: int = Field(..., ge=0)
    error_rate: float = Field(..., ge=0.0, le=1.0)
    active_agent_ids: List[str] = Field(default_factory=list)
    recent_operations: List[Dict[str, Any]] = Field(default_factory=list, max_items=20)
    metrics: Dict[str, int] = Field(default_factory=dict)


class ComplexityDistribution(BaseModel):
    """Distribution of queries by complexity"""
    simple: int = Field(0, ge=0)
    standard: int = Field(0, ge=0)
    complex: int = Field(0, ge=0)
    critical: int = Field(0, ge=0)


class SystemMetricsResponse(BaseModel):
    """Response model for system metrics"""
    flow_metrics: Dict[str, Any] = Field(..., description="Flow manager metrics")
    timestamp: datetime
    
    @validator('flow_metrics')
    def validate_flow_metrics(cls, v):
        """Ensure required fields are present"""
        required_fields = ['total_queries', 'approved_insights', 'rejected_insights']
        for field in required_fields:
            if field not in v:
                raise ValueError(f"Missing required field: {field}")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "flow_metrics": {
                    "total_queries": 1250,
                    "approved_insights": 1180,
                    "rejected_insights": 70,
                    "avg_processing_time_ms": 1452.3,
                    "complexity_distribution": {
                        "simple": 450,
                        "standard": 650,
                        "complex": 125,
                        "critical": 25
                    },
                    "active_flows": 3,
                    "total_flows": 1250,
                    "approval_rate": 0.944,
                    "cache_size": 150,
                    "cache_hit_rate": "Not tracked"
                },
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }


# Authentication Models
class UserInfoResponse(BaseModel):
    """Response model for user information"""
    uid: str = Field(..., description="User ID")
    email: Optional[str] = Field(None, description="User email")
    email_verified: bool = Field(False, description="Whether email is verified")
    display_name: Optional[str] = Field(None, description="Display name")
    dealership_id: Optional[str] = Field(None, description="Associated dealership")
    roles: List[str] = Field(default_factory=list, description="User roles")
    is_admin: bool = Field(False, description="Whether user is admin")
    
    class Config:
        schema_extra = {
            "example": {
                "uid": "user123",
                "email": "john.doe@dealership.com",
                "email_verified": True,
                "display_name": "John Doe",
                "dealership_id": "dealer_123",
                "roles": ["analyst", "manager"],
                "is_admin": False
            }
        }


class CreateUserRequest(BaseModel):
    """Request model for creating users (admin only)"""
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password", min_length=8)
    display_name: Optional[str] = Field(None, description="Display name")
    dealership_id: Optional[str] = Field(None, description="Dealership to associate with user")
    
    @validator('email')
    def validate_email(cls, v):
        return InputValidator.validate_email(v)
    
    @validator('dealership_id')
    def validate_dealership_id(cls, v):
        if v:
            return InputValidator.validate_dealership_id(v)
        return v
    
    @validator('display_name')
    def validate_display_name(cls, v):
        if v and len(v) > 100:
            raise ValueError("Display name too long")
        return v


class CreateUserResponse(BaseModel):
    """Response model for user creation"""
    uid: str
    email: str
    display_name: Optional[str] = None


# Webhook Models
class MailgunWebhookResponse(BaseModel):
    """Response model for Mailgun webhook processing"""
    status: str = Field(..., description="Processing status")
    message: Optional[str] = Field(None, description="Additional information")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "processed",
                "message": "Email processed and insight sent"
            }
        }