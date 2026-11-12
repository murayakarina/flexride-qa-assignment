"""Checks the API is reachable before the real tests run."""
from conftest import TIMEOUT


def test_api_is_up(api, base_url):
    response = api.get(f"{base_url}/ping", timeout=TIMEOUT)
    # Restful-Booker returns 201 for /ping (documented quirk).
    assert response.status_code == 201
