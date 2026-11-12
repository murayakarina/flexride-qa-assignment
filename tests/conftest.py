"""Shared fixtures for the Restful-Booker API tests."""
import os
import uuid
from datetime import date, timedelta

import pytest
import requests

BASE_URL = os.getenv("BOOKER_BASE_URL", "https://restful-booker.herokuapp.com")
# Public demo credentials from the Restful-Booker documentation; override with env vars if needed.
USERNAME = os.getenv("BOOKER_USERNAME", "admin")
PASSWORD = os.getenv("BOOKER_PASSWORD", "password123")
TIMEOUT = 15


def future_date(days_ahead):
    """An ISO date relative to today, so test dates never drift into the past."""
    return (date.today() + timedelta(days=days_ahead)).isoformat()


@pytest.fixture(scope="session")
def base_url():
    return BASE_URL


@pytest.fixture(scope="session")
def api():
    """A requests session that sends and accepts JSON."""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json", "Accept": "application/json"})
    yield session
    session.close()


@pytest.fixture(scope="session")
def token(api, base_url):
    """A valid auth token for update and delete requests."""
    response = api.post(f"{base_url}/auth", json={"username": USERNAME, "password": PASSWORD}, timeout=TIMEOUT)
    response.raise_for_status()
    body = response.json()
    # Restful-Booker returns 200 even for bad credentials, so check the body for a clear failure message.
    assert "token" in body, f"Auth failed, so update/delete tests cannot run: {body}"
    return body["token"]


@pytest.fixture
def booking_payload():
    """A valid booking body. Each call gets a unique last name so tests never share data."""
    return {
        "firstname": "QA",
        "lastname": f"Test-{uuid.uuid4().hex[:8]}",
        "totalprice": 150,
        "depositpaid": True,
        "bookingdates": {"checkin": future_date(30), "checkout": future_date(34)},
        "additionalneeds": "Breakfast",
    }


@pytest.fixture
def created_booking(api, base_url, token, booking_payload):
    """Creates a booking for the test, then deletes it afterwards (ignoring it if the test already did)."""
    response = api.post(f"{base_url}/booking", json=booking_payload, timeout=TIMEOUT)
    response.raise_for_status()
    booking_id = response.json()["bookingid"]
    yield booking_id, booking_payload
    api.delete(f"{base_url}/booking/{booking_id}", cookies={"token": token}, timeout=TIMEOUT)
