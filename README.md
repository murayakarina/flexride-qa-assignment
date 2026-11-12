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
| Negative | Invalid dates (`not-a-date`, `2030-02-30`) are rejected |
| Boundary | Negative total price is rejected |

Tests marked `known_api_bug` assert what the API *should* do. They fail against the current API and are left failing on purpose rather than adjusted to pass.

## Results summary

Run on 12 Nov 2026: **11 passed, 8 failed.** The 8 failing tests come from **5 distinct issues** (some tests run the same check with several inputs). None of the failures is a problem in the tests themselves.

Restful-Booker's documentation does not define validation rules, so I have separated issues that are defects whatever the requirements are from ones that depend on a business rule I assumed.

| # | Issue | Failing tests | Classification | What happens |
|---|---|---|---|---|
| 1 | Missing required fields crash the server | 3 (`lastname`, `totalprice`, `bookingdates`) | **Defect** whatever the requirements: client input should never cause a 500 | Returns **500 Internal Server Error** instead of 400 |
| 2 | Invalid dates are stored as corrupt or altered data | 2 (`not-a-date`, `2030-02-30`) | **Defect** whatever the requirements: data is corrupted or silently changed | `not-a-date` is stored as `0NaN-aN-aN`; 30 Feb silently becomes 2 Mar |
| 3 | Wrong password returns 200 | 1 | **Likely defect**: breaks HTTP convention; the docs do not specify the failure response | Returns **200** with `{"reason": "Bad credentials"}` instead of 401 |
| 4 | Checkout before checkin is accepted | 1 | **Assumed requirement**: to confirm with the product owner | Booking created with checkout 4 days before checkin |
| 5 | Negative total price is accepted | 1 | **Assumed requirement**: to confirm with the product owner | Booking created with `totalprice: -1` |

Observations not turned into failing tests (they match Restful-Booker's own documentation, but differ from common REST conventions; also noted as comments in the tests):
- Create returns 200 rather than 201 Created.
- Successful delete returns 201 rather than 200 or 204.
- Deleting an already deleted booking returns 405 rather than 404.
- A missing token returns 403 rather than 401.

**Why the GitHub Actions check is red:** the brief asked for tests to fail when the API is wrong rather than be adjusted to pass. To run only the tests expected to pass, use `pytest -m "not known_api_bug"`.

## AI tool notes

I used Claude (Anthropic) to draft this project. It first called the API directly to confirm real behaviour, then wrote the fixtures, tests and README. I then reviewed the draft and asked for these changes:

- **Grouped the 8 failures into 5 issues.** The draft reported "8 real API bugs", but several tests check the same root cause with different inputs. Counting them separately overstated the findings.
- **Separated defects from assumptions.** The draft called every failure a "real API bug". The documentation does not define rules for negative prices or date order, so I labelled those as assumed requirements to confirm, rather than claim more certainty than I have.
- **Replaced fixed 2027 dates with dates relative to today.** Fixed dates would eventually fall in the past and the tests would quietly start testing something else.
- **Made an authentication failure obvious.** The API returns 200 even for bad credentials, so a login problem showed up as a confusing `KeyError` in every test. It now fails with a clear message.
- **Made the cleanup check more robust.** It now reads the parsed JSON instead of searching the raw response text for "bookingid".
- **Added comments where tests accept documented quirks** (200 on create, 201 on delete), so a reader doesn't mistake them for oversights.

I kept the deliberately failing tests and the red CI check because the brief asked for that, and I ran the suite locally and in GitHub Actions to confirm the results.

## With more time I would

- Validate response schemas (field types and required fields) with `jsonschema`.
- Add PATCH (partial update) tests and `GET /booking` filter tests (by name and dates).
- Test boundary values for `totalprice` (0, very large, decimals) and string fields (empty, very long, special characters).
- Test that an expired token is rejected.
- Add an HTML or JUnit report to the GitHub Actions run.
