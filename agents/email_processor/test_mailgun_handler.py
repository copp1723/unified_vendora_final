import pytest
import json
from agents.email_processor.mailgun_handler import create_app
from insights.feedback_engine import FeedbackType

@pytest.fixture
def app():
    config = {
        'MAILGUN_PRIVATE_API_KEY': 'test_key', # Not used in feedback endpoint
        'DATA_STORAGE_PATH': '/tmp/vendora_test_data'
    }
    app = create_app(config)
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_task_feedback_valid_request(client):
    """Test valid feedback submission."""
    task_id = "test_task_123"
    feedback_data = {
        "user_id": "test_user",
        "feedback_type": FeedbackType.RATING.value,
        "rating": 5,
        "text_feedback": "This is great!"
    }
    response = client.post(
        f'/api/v1/task/{task_id}/feedback',
        data=json.dumps(feedback_data),
        content_type='application/json'
    )
    assert response.status_code == 201
    response_data = response.get_json()
    assert response_data["message"] == "Feedback received"
    assert response_data["task_id"] == task_id
    assert "feedback_id" in response_data

def test_task_feedback_invalid_request_body(client):
    """Test feedback submission with invalid request body."""
    task_id = "test_task_456"
    feedback_data = {
        "user_id": "test_user",
        # Missing feedback_type and other required fields
    }
    response = client.post(
        f'/api/v1/task/{task_id}/feedback',
        data=json.dumps(feedback_data),
        content_type='application/json'
    )
    assert response.status_code == 400
    response_data = response.get_json()
    assert response_data["error"] == "Invalid request body"

def test_task_feedback_invalid_feedback_type(client):
    """Test feedback submission with invalid feedback type."""
    task_id = "test_task_789"
    feedback_data = {
        "user_id": "test_user",
        "feedback_type": "invalid_type", # This should cause a validation error
        "rating": 3
    }
    response = client.post(
        f'/api/v1/task/{task_id}/feedback',
        data=json.dumps(feedback_data),
        content_type='application/json'
    )
    assert response.status_code == 400
    response_data = response.get_json()
    assert response_data["error"] == "Invalid request body"
    assert "details" in response_data

def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    assert response.get_json()['status'] == 'healthy'
