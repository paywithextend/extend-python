# Contributing

Use Python 3.11 or newer. CI validates Python 3.11–3.14.

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m ruff check extend tests tools
python -m pytest -q
```

On Windows, activate `.venv\Scripts\activate` instead. Notebook dependencies are
optional: install `.[notebooks]` if you need them.

## Testing

### Offline suite

`python -m pytest -q` runs the full offline suite and skips live tests. It requires
no account, credentials, `.env`, or network access. Real HTTP transports are blocked
for offline tests; use `httpx.MockTransport` with synthetic data.

- `test_endpoint_contracts.py` checks HTTP methods, paths, query parameters, bodies,
  multipart data, response envelopes, and coverage of every public resource method.
- `test_transport_security.py` checks credential isolation, destination restrictions,
  redirects, retry budgets, cancellation, and transport ownership.
- `test_client.py` checks authentication, empty responses, status errors, and DELETE.
- `test_live_support.py` verifies cleanup after failures and bounded matching checks.

Use the backend contract to define expectations. Do not change a fixture just to
agree with the implementation. Avoid mocking the resource method under test.

CI runs all these tests on each supported Python version, builds the package, then
runs the same tests against the installed wheel outside the source checkout.
To reproduce the wheel check locally:

```sh
python -m build
python -m venv /tmp/extend-wheel
/tmp/extend-wheel/bin/python -m pip install dist/*.whl pytest pytest-asyncio
/tmp/extend-wheel/bin/python tools/test_installed_wheel.py
```

The isolated environment must contain a wheel, not an editable installation.

### Live fixture setup

Live tests are optional for contributors. Maintainers should run relevant live
checks before releases or changes to endpoint contracts. A successful offline run
does not establish live authorization, delivery, or asynchronous service health.

1. Provision a dedicated test account and resources. Use staging or another approved
   test environment; the configuration selects the environment explicitly.
2. Copy `tests/fixtures/live.example.json` to `.live-tests/config.json`.
3. Set an active funding card ID and a dedicated, mutable transaction ID. Do not use
   a shared transaction or run concurrent jobs against the same transaction.
4. Configure test recipient/cardholder email addresses. Never point reminders at a
   real customer. Set `reminder_recipient` to the intended test email; the test checks it
   against the transaction recipient. The reminder transaction must require a receipt, have no attachment,
   and belong to the intended test recipient.
5. Export `EXTEND_TEST_API_KEY` and `EXTEND_TEST_API_SECRET` through your secret manager
   or shell session. No credentials belong in the JSON file or Git. The tests never
   load `.env` or use the application's `EXTEND_API_KEY` automatically.

Run read-only checks:

```sh
python -m pytest tests/test_integration.py --live-config .live-tests/config.json -q
```

Run card, category/label, transaction-expense, and receipt-upload workflows:

```sh
python -m pytest tests/test_integration.py --live-config .live-tests/config.json --live-writes -q
```

Receipt tests first check deletion of a unique nonexistent receipt. If the gateway
returns 403, they skip before uploading; that is a cleanup/route coverage gap, not a
passing upload test. A 401 or other unexpected response fails the check.

These tests create uniquely named resources. They register cleanup immediately
following creation, close cards, deactivate categories/labels, clear only the newly
created transaction-category assignment, and delete uploaded receipts. Categories,
labels, and cards may remain as inactive/closed audit records; cleanup does not mean
permanent erasure. Transactions and funding cards are never created or selected
arbitrarily by the test suite.

### Matching and reminders

For automatching, provision a synthetic receipt whose merchant, amount, currency,
and date match the fixture transaction, and put it beside the private JSON file.
Set `matching_receipt_file` to its relative filename. Then run:

```sh
python -m pytest tests/test_integration.py -k automatch --live-config .live-tests/config.json --live-writes --live-automatch -q
```

The test requires terminal `SUCCESS` and the exact expected transaction within
60 seconds. Job acceptance or a pending status is not a pass. This tests the matching
service as well as the SDK; missing fixtures must not be represented as successful
coverage. If a job times out, inspect the job before retrying: asynchronous work may
still be running after local cleanup.

Reminders are a separate, irreversible notification opt-in:

```sh
python -m pytest tests/test_integration.py -k reminder --live-config .live-tests/config.json --live-reminders -q
```

The test requires API acceptance; it does not claim inbox delivery. A rate limit
is a failure, not a successful send. Do not retry it blindly.

### Cleanup and reconciliation

Each mutating test writes a private `sdk-test-*.json` journal beside the fixture file,
recording created resource IDs and cleanup outcomes without credentials or payloads.
All registered cleanup actions are attempted even if assertions or another cleanup
action fail. A cleanup failure fails the run and leaves the journal for reconciliation.

A terminated process or ambiguous write timeout can leave resources behind. Inspect
journals and uniquely named `sdk-test-*` resources in the test account before repeating
a run. Never blindly retry a timed-out create operation. Keep journals private and
outside public CI artifacts. Do not publish live failure tracebacks, payloads, signed
URLs, or fixtures; report sanitized test names, statuses, and coverage gaps instead.

## Pull requests

Run lint and the full offline suite. Add contract tests for new resource methods and
regression tests for fixes. Describe live checks separately, including skipped checks
and cleanup failures. Use Conventional Commit titles, such as `fix: correct pagination`.
Do not commit credentials, private fixture IDs, or live response captures. See
[SECURITY.md](SECURITY.md) for reporting vulnerabilities.
