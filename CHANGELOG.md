# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-10-26

### Added

- `extend.auth` module providing reusable `Authorization` strategies (e.g., `BasicAuth`, `BearerAuth`).
- Support for injecting any `Authorization` implementation into both `APIClient` and `ExtendClient`.

### Changed

- **Breaking:** `APIClient` and `ExtendClient` constructors now require an `Authorization` instance instead of raw
  `api_key`/`api_secret` strings. Wrap credentials in `BasicAuth` or supply a different `Authorization` to upgrade.
- Updated documentation, examples, and tests to reflect the new initialization pattern.

## [1.2.2] - 2025-09-30

### Added

- `Transactions.get_transactions` now accepts multiple status values plus a `missing_expense_categories` flag to focus
  on
  records that still need categorization.
- Expanded unit and integration coverage validating the new filters along with stricter date-range assertions.

### Changed

- Transaction queries now send API-native parameter names (`perPage`, `since`, `until`) and emit `receiptStatus`/
  `expenseCategoryStatuses` lists whenever those filters are active.
- Status inputs are validated and normalized to uppercase before requests to avoid accidental API errors when multiple
  values are provided.

## [1.2.1] - 2025-04-11

### Added

- A `receipt_missing` flag on transaction listings for fetching only records that still need receipts, plus helper
  utilities/tests that assert attachment counts against that filter.

### Changed

- Receipt reminder flows now explicitly request `receipt_missing=True`, and the integration test tolerates HTTP 429
  rate limits while still verifying behavior.
- Transaction listing tests share a `get_transactions_from_response` helper to keep assertions consistent.

## [1.2.0] - 2025-04-10

### Added

- `Transactions.send_receipt_reminder` for nudging cardholders, with accompanying unit and integration tests.
- `APIClient.post_multipart` and a shared `_send_request` helper, enabling consistent handling of multipart uploads and
  HTTP verbs.

### Changed

- All HTTP methods now funnel through `_send_request`, unifying timeout/error handling and simplifying future
  instrumentation.

## [1.1.0] - 2025-04-08

### Added

- New `ReceiptCapture` resource (exposed via `ExtendClient.receipt_capture`) that supports bulk receipt automatching and
  status polling.
- Tests covering the new receipt-capture endpoints alongside improvements to receipt attachments and documentation.

## [1.0.0] - 2025-04-04

### Added

- First public release of the async Extend Python SDK, including typed models, validation utilities, and resource
  wrappers for credit cards, virtual cards, transactions, expense data, and receipt uploads.
- Developer tooling essentials: packaging metadata, Makefile shortcuts, `.env` template, CI release workflow, and
  contribution guidelines.
- Comprehensive automation (unit + integration tests) plus the initial Jupyter notebook for interactive API
  exploration.

### Changed

- None (initial release)

### Deprecated

- None (initial release)

### Removed

- None (initial release)

### Fixed

- None (initial release)

### Security

- None (initial release) 
