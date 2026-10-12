from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

import src.app as api


initial_activities = deepcopy(api.activities)


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(api, "activities", deepcopy(initial_activities))
    return TestClient(api.app)


def test_root_redirects_to_static_index(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_data(client):
    response = client.get("/activities")

    assert response.status_code == 200
    activities = response.json()
    assert set(activities) == set(initial_activities)
    assert activities["Chess Club"]["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]
    assert activities["Chess Club"]["max_participants"] == 12


def test_signup_adds_participant(client):
    activity_name = "Soccer Team"
    email = "student@mergington.edu"
    response = client.post(
        f"/activities/{quote(activity_name, safe='')}/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {activity_name}"
    }
    assert api.activities[activity_name]["participants"] == [email]


@pytest.mark.parametrize(
    ("activity_name", "email", "expected_status"),
    [
        ("Unknown Activity", "student@mergington.edu", 404),
        ("Chess Club", "michael@mergington.edu", 400),
    ],
)
def test_signup_rejects_invalid_request(client, activity_name, email, expected_status):
    response = client.post(
        f"/activities/{quote(activity_name, safe='')}/signup",
        params={"email": email},
    )

    assert response.status_code == expected_status


def test_signup_requires_email(client):
    response = client.post("/activities/Chess%20Club/signup")

    assert response.status_code == 422


def test_unregister_removes_participant(client):
    activity_name = "Chess Club"
    email = "michael@mergington.edu"
    response = client.delete(
        f"/activities/{quote(activity_name, safe='')}/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from {activity_name}"
    }
    assert email not in api.activities[activity_name]["participants"]


@pytest.mark.parametrize(
    ("activity_name", "email"),
    [
        ("Unknown Activity", "student@mergington.edu"),
        ("Chess Club", "student@mergington.edu"),
    ],
)
def test_unregister_rejects_invalid_request(client, activity_name, email):
    response = client.delete(
        f"/activities/{quote(activity_name, safe='')}/signup",
        params={"email": email},
    )

    assert response.status_code == 404