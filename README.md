# Restful-Booker API tests (FlexRide QA assignment, Part C)

Automated API tests for https://restful-booker.herokuapp.com using Python, pytest and requests.

## Run the tests

Requires Python 3.10 or later. Run these from the project folder (the one containing `pytest.ini`):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
```

To run only the tests expected to pass (skipping the ones that document API bugs):

```bash
pytest -m "not known_api_bug"
```

The tests use the public demo credentials from the Restful-Booker docs. To override them, set `BOOKER_USERNAME`, `BOOKER_PASSWORD` or `BOOKER_BASE_URL`.

Each test creates its own booking and deletes it afterwards, so the suite does not depend on existing data (the demo data resets every 10 minutes). Negative tests also delete any booking the API wrongly accepts.

## What is covered

| Area | Test |
|---|---|
| Health | API responds to `/ping` |
| Auth | Get a token with valid credentials |
| Auth | Wrong password is rejected with 401 |
| Create | Created booking matches the request and has a numeric ID |
| Read | Booking read back by ID matches what was sent |
| Read | Unknown booking ID returns 404 |
| Update | PUT with a valid token updates the booking, and the change is saved |
| Update | PUT with no token or an invalid token returns 403 and leaves the booking unchanged |
| Delete | DELETE with no token or an invalid token returns 403 and the booking still exists |
| Delete | DELETE with a valid token removes the booking, and GET then returns 404 |
| Negative | Missing `lastname`, `totalprice` or `bookingdates` returns 400 |
| Boundary | Checkout before checkin is rejected |
| Negative | Invalid dates (`not-a-date`, `2027-02-30`) are rejected |
| Boundary | Negative total price is rejected |

Tests marked `known_api_bug` assert what the API *should* do. They fail against the current API and are left failing on purpose rather than adjusted to pass.

## Results summary

Run on 12 Nov 2026: **11 passed, 8 failed.** All 8 failures are real API bugs, not test problems.

| Test | Result | Real API bug? | What happens |
|---|---|---|---|
| Auth, create, read, update, delete (happy paths) | Pass | - | Behaves as documented |
| No token / invalid token on PUT and DELETE | Pass | - | 403, data unchanged |
| Unknown booking returns 404 | Pass | - | 404 |
| Wrong password rejected | **Fail** | Yes | Returns **200** with `{"reason": "Bad credentials"}` instead of 401 |
| Missing `lastname` / `totalprice` / `bookingdates` | **Fail** (3) | Yes | Returns **500 Internal Server Error** instead of 400. Bad input crashes the server |
| Checkout before checkin | **Fail** | Yes | Booking created with checkout 4 days before checkin |
| Checkin `not-a-date` | **Fail** | Yes | Accepted and stored as `0NaN-aN-aN` (corrupt data) |
| Checkin `2027-02-30` | **Fail** | Yes | Accepted and silently changed to `2027-03-02` |
| Negative total price | **Fail** | Yes | Booking created with `totalprice: -1` |

Observations not turned into failing tests (they match Restful-Booker's own documentation, but differ from common REST conventions):
- Create returns 200 rather than 201 Created.
- Successful delete returns 201 rather than 200 or 204.
- Deleting an already deleted booking returns 405 rather than 404.
- A missing token returns 403 rather than 401.

## AI tool notes

Claude (Anthropic) wrote the first draft of the project: fixtures, test cases, the `known_api_bug` marker and this README. Before writing tests it called the API directly to confirm real behaviour, so expected results were based on observed responses and the documentation rather than guesses.

<!-- Replace with your own words: what you reviewed, changed or rejected. For example: -->
<!-- I reviewed every test against the API docs, ran the suite myself, and changed/rejected ... -->

## With more time I would

- Validate response schemas (field types and required fields) with `jsonschema`.
- Add PATCH (partial update) tests and `GET /booking` filter tests (by name and dates).
- Test boundary values for `totalprice` (0, very large, decimals) and string fields (empty, very long, special characters).
- Test that an expired token is rejected.
- Add an HTML or JUnit report to the GitHub Actions run.
