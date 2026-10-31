"""Explicit environment selection; importing this module has no side effects."""
import os

API_VERSION = "application/vnd.paywithextend.v2021-03-12+json"
API_HOSTS = {
    "stage": "apiv2-stage.paywithextend.com",
    "prod": "apiv2.paywithextend.com",
}


def resolve_environment(environment: str | None = None) -> str:
    """Resolve an explicitly selected environment, never defaulting to production."""
    selected = environment if environment is not None else os.environ.get("ENV")
    if selected not in API_HOSTS:
        raise ValueError("Choose environment='stage' or environment='prod' (or set ENV explicitly)")
    return selected


__all__ = ["API_VERSION", "API_HOSTS", "resolve_environment"]
