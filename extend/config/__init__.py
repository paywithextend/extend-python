import os

from dotenv import load_dotenv

load_dotenv()

env = os.getenv("ENV", "dev")

if env == "stage":
    from .config_stage import API_HOST, API_VERSION
elif env == "prod":
    from .config_prod import API_HOST, API_VERSION
else:
    from .config_prod import API_HOST, API_VERSION

__all__ = [
    "API_HOST",
    "API_VERSION"
]
