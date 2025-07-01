
import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.auth.firebase_auth import FirebaseUser, get_current_user

# Create a TestClient instance for making requests to the app
client = TestClient(app)

# A sample FirebaseUser object for authenticated tests
fake_user = FirebaseUser(
    uid="test_user_123",
    email="test@example.com",
    email_verified=True,
    display_name="Test User",
)

# Dependency override to mock authentication
def get_current_user_override():
    """Override for get_current_user that returns a fake user."""
    return fake_user

# Apply the override to the app's dependency
app.dependency_overrides[get_current_user] = get_current_user_override

# Sample Mailgun webhook payload (as JSON)
# In a real scenario, this would be more detailed
mailgun_payload = {
    "sender": "test@example.com",
    "recipient": "webhook@vendora.com",
    "subject": "Test CSV File",
    "body-plain": "Here is the test CSV file.",
    "message-headers": '[]' # Empty JSON array as string for headers
}

def test_webhook_unauthenticated():
    """
    Test that accessing the /webhook/mailgun endpoint without an
    Authorization header fails with a 403 Forbidden error.
    """
    # Create a temporary client without the dependency override to test the real auth flow
    unauthenticated_client = TestClient(app, raise_server_exceptions=False)
    unauthenticated_client.app.dependency_overrides = {} # Clear overrides

    response = unauthenticated_client.post("/webhook/mailgun", json=mailgun_payload)
    
    # Without a token, FastAPI's Security dependency should return a 403
    assert response.status_code == 403
    assert response.json() == {"detail": "Authentication required"}

def test_webhook_invalid_token():
    """
    Test that accessing the endpoint with a clearly invalid token
    fails with a 401 Unauthorized error.
    """
    # Create a temporary client without the dependency override
    unauthenticated_client = TestClient(app, raise_server_exceptions=False)
    unauthenticated_client.app.dependency_overrides = {} # Clear overrides

    headers = {"Authorization": "Bearer invalidtoken123"}
    response = unauthenticated_client.post("/webhook/mailgun", json=mailgun_payload, headers=headers)
    
    # The FirebaseAuthHandler should reject the token and return a 401
    assert response.status_code == 401
    assert "Could not validate authentication token" in response.json()["detail"]

def test_webhook_authenticated_request():
    """
    Test that an authenticated request (using the dependency override)
    can access the webhook endpoint.
    
    Note: This test verifies authentication is bypassed. It may still fail
    if the Mailgun handler itself has issues with the test data, but the
    status code should NOT be 401 or 403.
    """
    # This client uses the overridden dependency
    response = client.post("/webhook/mailgun", json=mailgun_payload)
    
    # We expect a status other than 401/403.
    # A 400 Bad Request is likely if the Mailgun handler finds the payload
    # is missing required fields for processing, which proves auth was successful.
    # A 500 might occur if the handler isn't initialized.
    assert response.status_code != 401
    assert response.status_code != 403
    
    print(f"Authenticated request to webhook received status: {response.status_code}")
    # In this case, since Mailgun handler is not fully configured, it might return an error
    # This is okay, as long as it's not an auth error
    if response.status_code == 400:
         assert "Processing failed" in response.json()["detail"]
    elif response.status_code == 500:
        assert "internal server error" in response.json()["detail"].lower()

