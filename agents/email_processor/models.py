from typing import Optional, Dict, Any
from pydantic import BaseModel
from insights.feedback_engine import FeedbackType

class FeedbackRequest(BaseModel):
    user_id: str
    feedback_type: FeedbackType
    rating: Optional[int] = None
    thumbs_up: Optional[bool] = None
    text_feedback: Optional[str] = None
    structured_feedback: Optional[Dict[str, Any]] = None
    expected_vs_actual: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
