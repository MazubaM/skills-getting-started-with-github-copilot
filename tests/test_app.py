import pytest
import copy
from fastapi.testclient import TestClient
from src.app import app, activities

client = TestClient(app, follow_redirects=False)

@pytest.fixture
def reset_activities():
    """Fixture to reset activities dict after each test for isolation."""
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)

def test_get_activities(reset_activities):
    # Arrange: Activities are loaded from app
    # Act
    response = client.get("/activities")
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data
    activity = data["Chess Club"]
    assert "description" in activity
    assert "schedule" in activity
    assert "max_participants" in activity
    assert "participants" in activity
    assert isinstance(activity["participants"], list)

def test_signup_success(reset_activities):
    # Arrange: Valid activity and new email
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"
    # Act
    response = client.post(f"/activities/{activity_name}/signup?email={email}")
    # Assert
    assert response.status_code == 200
    assert "Signed up" in response.json()["message"]
    # Verify added
    resp = client.get("/activities")
    data = resp.json()
    assert email in data[activity_name]["participants"]

def test_signup_duplicate(reset_activities):
    # Arrange: Sign up once
    activity_name = "Programming Class"
    email = "dup@mergington.edu"
    client.post(f"/activities/{activity_name}/signup?email={email}")
    # Act: Try to sign up again
    response = client.post(f"/activities/{activity_name}/signup?email={email}")
    # Assert
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"]

def test_signup_invalid_activity(reset_activities):
    # Arrange: Nonexistent activity
    # Act
    response = client.post("/activities/Nonexistent/signup?email=test@mergington.edu")
    # Assert
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]

def test_signup_full(reset_activities):
    # Arrange: Make an activity full
    activity_name = "Tennis Club"
    activities[activity_name]["max_participants"] = 1  # Set to 1
    # It already has 2 participants, so full
    email = "extra@mergington.edu"
    # Act
    response = client.post(f"/activities/{activity_name}/signup?email={email}")
    # Assert
    assert response.status_code == 400
    assert "Activity is full" in response.json()["detail"]

def test_delete_success(reset_activities):
    # Arrange: Sign up first
    activity_name = "Digital Art"
    email = "del@mergington.edu"
    client.post(f"/activities/{activity_name}/signup?email={email}")
    # Act
    response = client.delete(f"/activities/{activity_name}/participants/{email}")
    # Assert
    assert response.status_code == 200
    assert "Unregistered" in response.json()["message"]
    # Verify removed
    resp = client.get("/activities")
    data = resp.json()
    assert email not in data[activity_name]["participants"]

def test_delete_not_signed_up(reset_activities):
    # Arrange: Email not signed up
    # Act
    response = client.delete("/activities/Chess%20Club/participants/nosignup@mergington.edu")
    # Assert
    assert response.status_code == 400
    assert "not signed up" in response.json()["detail"]

def test_delete_invalid_activity(reset_activities):
    # Arrange: Invalid activity
    # Act
    response = client.delete("/activities/Invalid/participants/test@mergington.edu")
    # Assert
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]

def test_root_redirect(reset_activities):
    # Arrange: No special setup
    # Act
    response = client.get("/")
    # Assert
    assert response.status_code == 307
    assert "/static/index.html" in response.headers["location"]