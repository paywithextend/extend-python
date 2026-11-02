# Migrating from 2.x to 3.x

- Python 3.11 or newer is required. CI checks 3.11, 3.12, 3.13 and 3.14.
- Select environment="stage" or environment="prod" when constructing a client.
  An explicitly set ENV=stage or ENV=prod is supported for migration. Missing,
  misspelled and legacy ENV=dev values fail at client construction. Import is safe.
- The SDK no longer loads .env or depends on python-dotenv. If an application
  needs dotenv, load it explicitly before constructing the client.
- Use async with ExtendClient(...) or await client.aclose(). An injected
  http_client remains owned by its caller.
- Authorization providers are queried per request; client.headers is a snapshot,
  not a mutable configuration surface. shared_instance now returns an independent
  client to prevent cross-user credential reuse.
- Low-level paths must start with a single slash and contain only unencoded
  endpoint characters. Use params for query strings. Absolute URLs, percent
  escapes, dot segments and authority-like paths are rejected.
- Only safe GET requests retry (429/502/503/504 or transport failures), within a
  time budget. Writes never retry automatically. Reconcile uncertain writes
  before trying again.
- ExtendAPIError preserves HTTP status, request_id and retry_after. Its display
  text omits response bodies and URLs. Inspect the response only in trusted code.
- client.api_client is the supported low-level transport for additional Extend
  endpoints. It enforces the same origin and lifecycle rules.
- Sensitive request payloads are no longer printed.

## Releases

Release publication is manual, from a versioned tag reachable from main.
Run the release workflow on main with that tag after review and CI.
The protected pypi environment and Trusted Publisher must already be configured.
The workflow tests the source, builds a wheel, tests that wheel and publishes the
same artifacts. Merging a PR does not publish a package. See [RELEASING.md](RELEASING.md)
for publisher configuration, tagging and publication verification.

## Resource contracts

- Card/label/member pages are zero-based; transaction report pages are one-based.
  Transaction reports return a `report` envelope. A full-page `count` is a
  continuation sentinel; call `transactions.count_transactions(**filters)` for
  an exact count. Listing and counting use the same filter mapping.
- Transaction filters now accept `statuses`, `receipt_statuses`,
  `expense_category_statuses`, `credit_card_id`, and `date_type="Clear"`.
  Clearing-date ranges use `sinceClearedAt`/`untilClearedAt`. Explicit false
  missing-data filters select `Attached`; omit them to leave that filter unset.
- Credit-card listing supports `type` and `sort_field`. Both server spellings
  `status` and `statuses` are valid; the SDK uses `status` for its single value.
  REJECTED virtual cards and NEEDS_VERIFICATION/NOT_APPLICABLE credit cards are
  accepted by status validation.
- Recurrence dictionaries accept the documented camelCase keys (and legacy
  snake_case aliases). Monthly days 29–31 are valid; the service handles shorter
  months. Invalid period/terminator combinations fail without a request.
- Card local dates remain `YYYY-MM-DD`, preserving account-timezone semantics.
  ISO timestamps retain their timezone. They are no longer changed to UTC
  midnight/end-of-day. Empty notes clear notes; omitted notes remain omitted.
  Ordinary card updates require display name and balance; balances must be
  integer cents from 100 through 2,100,000,000. Business/state checks stay on
  the server. `create_virtual_card` also accepts `valid_from`.
- Resource IDs must be single identifiers. Nested null expense-label values
  remain null, allowing explicit label removal.
- `expense_data.get_expense_category_label`, `organizations` and `users` now
  provide resource wrappers. Category queries accept `transaction_id` for
  applicable custom fields; create/update support separate transaction/card
  required flags. Responses retain their native envelopes, nulls and currencies.
- Receipt upload accepts optional `filename`/`content_type` for a prevalidated
  binary stream, whose ownership remains with the caller. Reminder success has
  no response body and returns `None`. Policy reads return metadata and never
  fetch signed URLs automatically.
- These resources require user-scoped credentials and remain subject to server
  permissions, account configuration and feature availability. Enterprise
  service keys are not interchangeable with user API keys. Contract fixtures
  are synthetic; they do not establish deployed permissions or live end-to-end
  behavior. The SDK intentionally exposes a subset of the API, not every UI
  workflow, approval, bulk operation or vault-secret operation.
