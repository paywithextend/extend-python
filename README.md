# Extend API Client

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A Python client for the Extend API, providing a simple and intuitive interface for managing virtual cards, transactions, and more.

## Features

- Create and manage virtual cards
- Handle recurring card operations
- Track transactions
- Full async/await support
- Type hints and validation
- Comprehensive test suite

## Installation

### From PyPI

```bash
pip install extend-api-client
```

### From Source

```bash
git clone https://github.com/yourusername/extend-api-client.git
cd extend-api-client
pip install -e .
```

## Quick Start

```python
import asyncio
from extend import ExtendAPI

async def main():
    # Initialize the client
    client = ExtendAPI(
        api_key="your-api-key",
        api_secret="your-api-secret"
    )
    
    # Get all virtual cards
    cards = await client.get_virtual_cards()
    print("Virtual Cards:", cards)
    
    # Get all transactions
    transactions = await client.get_transactions()
    print("Transactions:", transactions)

# Run the async function
asyncio.run(main())
```

## Environment Variables

The following environment variables are required for integration tests and examples:

- `EXTEND_API_KEY`: Your Extend API key
- `EXTEND_API_SECRET`: Your Extend API secret
- `EXTEND_TEST_RECIPIENT`: Email address for test card recipient
- `EXTEND_TEST_CARDHOLDER`: Email address for test cardholder

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/extend-api-client.git
   cd extend-api-client
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
   # Run all tests
   pytest
   
   # Run only unit tests
   pytest tests/test_client.py
   
   # Run only integration tests
   pytest tests/test_integration.py
   ```

5. Format code:
   ```bash
   black .
   isort .
   ```

## Testing

The project includes both unit tests and integration tests:

- Unit tests (`tests/test_client.py`): Test the client's internal logic and validation
- Integration tests (`tests/test_integration.py`): Test actual API interactions
- Example notebook (`notebooks/api_testing.ipynb`): Interactive examples

To run integration tests, make sure you have set up the required environment variables.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Extend API Documentation](https://docs.extend.com)
- [httpx](https://www.python-httpx.org/) for async HTTP requests
