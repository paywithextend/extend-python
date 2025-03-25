# Contributing to Extend API Client

Thank you for your interest in contributing to the Extend API Client! This document provides guidelines and steps for contributing.

## Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/your-username/extend-api-client.git
   cd extend-api-client
   ```
3. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

## Code Style

This project uses:
- [black](https://github.com/psf/black) for code formatting
- [isort](https://github.com/pycqa/isort) for import sorting

Before submitting a PR, please run:
```bash
black .
isort .
```

## Testing

We have two types of tests:
1. Unit tests (`tests/test_client.py`)
2. Integration tests (`tests/test_integration.py`)

Run all tests:
```bash
pytest
```

Run only unit tests:
```bash
pytest tests/test_client.py
```

Run only integration tests:
```bash
pytest tests/test_integration.py
```

### Integration Tests

Integration tests require environment variables:
- `EXTEND_API_KEY`
- `EXTEND_API_SECRET`
- `EXTEND_TEST_RECIPIENT`
- `EXTEND_TEST_CARDHOLDER`

## Pull Request Process

1. Create a new branch for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and commit them:
   ```bash
   git commit -m "Description of your changes"
   ```

3. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

4. Create a Pull Request from your fork to the main repository

## Code Review Guidelines

- Ensure all tests pass
- Follow the existing code style
- Add tests for new functionality
- Update documentation as needed
- Keep commits focused and atomic

## Documentation

- Update the README.md if you add new features
- Add docstrings to new functions and classes
- Update the CHANGELOG.md with your changes

## Questions?

If you have any questions, feel free to:
1. Open an issue
2. Contact the maintainers
3. Check the [Extend API Documentation](https://docs.extend.com)

Thank you for contributing! 