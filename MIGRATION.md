# Migrating from 2.x to 3.x

- Python 3.11 or newer is required. CI checks 3.11, 3.12 and 3.13.
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

Release publication is manual, from a versioned tag reachable from development.
Run the release workflow on development with that tag after review and CI.
The protected pypi environment and Trusted Publisher must already be configured.
The workflow tests the source, builds a wheel, tests that wheel and publishes the
same artifacts. Merging a PR does not publish a package.
