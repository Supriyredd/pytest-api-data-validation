# PyTest API & Data Validation

![tests](https://github.com/Supriyredd/pytest-api-data-validation/actions/workflows/tests.yml/badge.svg)

API contract, business-rule and **API-to-database reconciliation** tests in Python (PyTest, Requests, jsonschema, pandas). The system under test is a small pharmacy REST API (Flask + SQLite) that ships in the repo and is filled with **synthetic** data.

> **Portfolio project.** Independently written with synthetic data. No employer or client code, data, schemas or configuration. The patient records are generated (MRNs start with `SYN`).

## What this repository demonstrates

| Skill | Where to look |
| --- | --- |
| API client with timeouts, safe retries (GET only) and request logging | `qa_tools/client.py` |
| Session-scoped fixtures that start the API on a free port | `tests/conftest.py` |
| Auth, pagination and negative tests with `parametrize` | `tests/test_api_contract.py` |
| JSON schema validation | `tests/schemas.py` |
| Business rules verified in both the response and the database | `tests/test_refill_rules.py` |
| API-to-DB reconciliation with pandas and a CSV mismatch report | `qa_tools/reconcile.py`, `tests/test_reconciliation.py` |
| A test for the test tool itself (the reconciler must catch mismatches) | `test_reconcile_detects_mismatches` |
| Data-quality rules (unique keys, orphans, ranges) in SQL | `test_data_quality_rules` |
| CI across Python 3.11–3.13 with HTML and JUnit reports | `.github/workflows/tests.yml` |

## Test strategy

1. **Contract:** every endpoint returns the documented shape (jsonschema), protected endpoints reject missing or wrong tokens, bad input returns 400/404/409.
2. **Business rules:** refilling a prescription decrements refills and sets status, and the change is checked in SQLite, not only in the response. Cancelled or exhausted prescriptions return 409 and leave the data unchanged.
3. **Reconciliation:** the suite pages through the whole API and compares it to the database row by row. Any missing row or changed value fails the build and is written to `reports/*.csv` for triage.
4. **Independence:** each test selects its own data from the database, so tests pass in any order.

## Run it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest                                   # starts the demo API automatically
pytest -m data                           # reconciliation only
pytest --html=reports/report.html --self-contained-html
```

To point the suite at another deployment of the same API, set `BASE_URL` and `API_TOKEN` (see `.env.example`). Never commit real tokens; in CI they come from repository secrets.

## Results

Local run: **20 tests, 20 passed in 0.9 s**; also passes with test files run in reverse order.

## Limitations and next steps

- SQLite stands in for an enterprise database; the same pattern works with an Oracle or SQL Server driver.
- Next: contract tests with Pact, a k6 load profile for `/patients`, property-based tests with Hypothesis.

## About the author

Supriya Dubbaka, Senior SDET. [LinkedIn](https://www.linkedin.com/in/supriya-dubbaka-64ba7532a/)

Built with AI-assisted development tools (GitHub Copilot / Claude); all code reviewed and run before publishing.

## License

MIT
