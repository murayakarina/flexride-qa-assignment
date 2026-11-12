"""Booking API tests for Restful-Booker.

Tests marked known_api_bug assert what the API *should* do and currently fail.
They are left failing on purpose (see README results summary).
"""
import pytest

from conftest import TIMEOUT, USERNAME


def delete_if_created(api, base_url, token, response):
    """Clean up a booking that a negative test expected to be rejected but the API accepted."""
    if response.status_code == 200 and "bookingid" in response.text:
        api.delete(f"{base_url}/booking/{response.json()['bookingid']}", cookies={"token": token}, timeout=TIMEOUT)


# --- Auth ---

def test_get_auth_token(token):
    assert isinstance(token, str)
    assert len(token) > 0


@pytest.mark.known_api_bug
def test_auth_with_wrong_password_is_rejected(api, base_url):
    response = api.post(f"{base_url}/auth", json={"username": USERNAME, "password": "wrong-password"}, timeout=TIMEOUT)
    assert "token" not in response.json()
    # Wrong credentials should return 401 Unauthorized, not 200.
    assert response.status_code == 401


# --- Create and read ---

def test_create_booking_matches_request(api, base_url, token, booking_payload):
    response = api.post(f"{base_url}/booking", json=booking_payload, timeout=TIMEOUT)
    try:
        assert response.status_code == 200
        body = response.json()
        assert isinstance(body["bookingid"], int)
        assert body["booking"] == booking_payload
    finally:
        delete_if_created(api, base_url, token, response)


def test_read_booking_by_id(api, base_url, created_booking):
    booking_id, sent = created_booking
    response = api.get(f"{base_url}/booking/{booking_id}", timeout=TIMEOUT)
    assert response.status_code == 200
    assert response.json() == sent


def test_read_unknown_booking_returns_404(api, base_url):
    response = api.get(f"{base_url}/booking/999999999", timeout=TIMEOUT)
    assert response.status_code == 404


# --- Update ---

def test_update_booking_with_valid_token(api, base_url, token, created_booking):
    booking_id, sent = created_booking
    updated = {**sent, "firstname": "Updated", "totalprice": 275, "additionalneeds": "Late checkout"}

    response = api.put(f"{base_url}/booking/{booking_id}", json=updated, cookies={"token": token}, timeout=TIMEOUT)
    assert response.status_code == 200
    assert response.json() == updated

    # Confirm the change was saved, not just echoed back.
    assert api.get(f"{base_url}/booking/{booking_id}", timeout=TIMEOUT).json() == updated


@pytest.mark.parametrize("cookies", [None, {"token": "invalid-token"}], ids=["no_token", "invalid_token"])
def test_update_without_valid_token_is_rejected(api, base_url, created_booking, cookies):
    booking_id, sent = created_booking
    response = api.put(f"{base_url}/booking/{booking_id}", json={**sent, "firstname": "Hacker"}, cookies=cookies, timeout=TIMEOUT)
    assert response.status_code == 403

    # The booking must be unchanged.
    assert api.get(f"{base_url}/booking/{booking_id}", timeout=TIMEOUT).json() == sent


# --- Delete ---

@pytest.mark.parametrize("cookies", [None, {"token": "invalid-token"}], ids=["no_token", "invalid_token"])
def test_delete_without_valid_token_is_rejected(api, base_url, created_booking, cookies):
    booking_id, _ = created_booking
    response = api.delete(f"{base_url}/booking/{booking_id}", cookies=cookies, timeout=TIMEOUT)
    assert response.status_code == 403

    # The booking must still exist.
    assert api.get(f"{base_url}/booking/{booking_id}", timeout=TIMEOUT).status_code == 200


def test_delete_booking_and_confirm_gone(api, base_url, token, created_booking):
    booking_id, _ = created_booking
    response = api.delete(f"{base_url}/booking/{booking_id}", cookies={"token": token}, timeout=TIMEOUT)
    # Restful-Booker documents 201 for a successful delete.
    assert response.status_code == 201

    assert api.get(f"{base_url}/booking/{booking_id}", timeout=TIMEOUT).status_code == 404


# --- Negative and boundary ---

@pytest.mark.known_api_bug
@pytest.mark.parametrize("missing_field", ["lastname", "totalprice", "bookingdates"])
def test_create_with_missing_required_field_returns_400(api, base_url, token, booking_payload, missing_field):
    del booking_payload[missing_field]
    response = api.post(f"{base_url}/booking", json=booking_payload, timeout=TIMEOUT)
    delete_if_created(api, base_url, token, response)
    # Bad input should be a 400 client error, not a 500 server error.
    assert response.status_code == 400


@pytest.mark.known_api_bug
def test_create_with_checkout_before_checkin_is_rejected(api, base_url, token, booking_payload):
    booking_payload["bookingdates"] = {"checkin": "2027-03-05", "checkout": "2027-03-01"}
    response = api.post(f"{base_url}/booking", json=booking_payload, timeout=TIMEOUT)
    delete_if_created(api, base_url, token, response)
    assert response.status_code == 400


@pytest.mark.known_api_bug
@pytest.mark.parametrize("bad_date", ["not-a-date", "2027-02-30"], ids=["text", "impossible_date"])
def test_create_with_invalid_date_is_rejected(api, base_url, token, booking_payload, bad_date):
    booking_payload["bookingdates"]["checkin"] = bad_date
    response = api.post(f"{base_url}/booking", json=booking_payload, timeout=TIMEOUT)
    stored = response.json()["booking"]["bookingdates"]["checkin"] if response.status_code == 200 else None
    delete_if_created(api, base_url, token, response)
    assert response.status_code == 400, f"API accepted {bad_date!r} and stored it as {stored!r}"


@pytest.mark.known_api_bug
def test_create_with_negative_price_is_rejected(api, base_url, token, booking_payload):
    booking_payload["totalprice"] = -1
    response = api.post(f"{base_url}/booking", json=booking_payload, timeout=TIMEOUT)
    delete_if_created(api, base_url, token, response)
    assert response.status_code == 400
