# extend-python

Python library for the Extend API

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Documentation](https://img.shields.io/badge/docs-stoplight-blue)](https://paywithextend.stoplight.io/)

A Python client for the Extend API, providing a simple and intuitive interface for managing virtual cards, transactions,
and more.

## Features

- Create and manage virtual cards
- Handle recurring card operations
- Track transactions
- Expense management

## Documentation

For detailed API documentation, please visit our [Stoplight documentation](https://paywithextend.stoplight.io/).

## Installation

### From PyPI

```bash
pip install paywithextend
```

### From Source

```bash
git clone https://github.com/paywithextend/extend-python.git
cd extend-python
pip install -e .
```

## Quick Start

Version 3 requires explicit environment selection and client cleanup. See
[the migration guide](MIGRATION.md) for security and compatibility changes.

```python
import asyncio
from extend import ExtendClient
from extend.auth import BasicAuth


async def main():
    # Initialize the client
    async with ExtendClient(
        auth=BasicAuth(
            "your-api-key",
            "your-api-secret",
        ),
        environment="stage",
    ) as client:
        response = await client.virtual_cards.get_virtual_cards()
        # Handle the result in your application; avoid logging financial payloads.


# Run the async function
asyncio.run(main())
```

### Using Custom Authorization

Both `ExtendClient` and `APIClient` accept reusable authorization strategies defined in `extend.auth`, enabling scenarios like JWT-based access or shared credentials across clients.

```python
from extend import ExtendClient
from extend.auth import BearerAuth

auth = BearerAuth(jwt_token="your-jwt-token")
client = ExtendClient(auth=auth, environment="stage")
# await client.aclose() when finished, or prefer async with.
```

If you want to work with the lower-level `APIClient` directly, you can pass any `Authorization` implementation:

```python
from extend.auth import BasicAuth
from extend.client import APIClient

api_client = APIClient(auth=BasicAuth("your-api-key", "your-api-secret"), environment="stage")
# await api_client.aclose() when finished.
```

## Environment Variables

Examples may read `EXTEND_API_KEY` and `EXTEND_API_SECRET` explicitly in application code.
The SDK and test suite do not automatically load `.env` files.
Live tests use separate `EXTEND_TEST_API_KEY` / `EXTEND_TEST_API_SECRET` variables and
an explicitly supplied private fixture file. See [Testing](CONTRIBUTING.md#testing).

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/paywithextend/extend-python.git
   cd extend-python
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

4. Run tests:
   ```bash
   # Complete offline suite; no account or credentials required.
   python -m pytest -q
   make lint
   ```

## Testing

The default suite verifies every resource's HTTP contract, authentication, errors,
transport security, retries, and cleanup without contacting Extend. CI runs it from
source and against an installed wheel on Python 3.11–3.14.

Live tests are opt-in and use explicitly provisioned resources. Writes, receipt
matching, and reminders each require explicit flags. See the
[contributor testing guide](CONTRIBUTING.md#testing) for fixture setup and cleanup.

## Contributing

We welcome contributions from the community! 

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Extend API Documentation](https://paywithextend.stoplight.io/)
- [httpx](https://www.python-httpx.org/) for async HTTP requests

### Endpoint availability

Server implementation, public gateway exposure, and account permissions are separate
requirements. Organization, member, policy, user, and individual-label helpers may
return 403 where the public gateway does not expose those routes. Receipt deletion
is also unavailable on some gateways even when upload is enabled. Offline contract
tests verify serialization; they do not establish deployed route availability.
