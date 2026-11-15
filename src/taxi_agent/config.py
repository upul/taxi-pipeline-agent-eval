import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

# Automatically locate the project root directory (3 levels up from src/taxi_agent/config.py)
ROOT_DIR = Path(__file__).resolve().parent.parent.parent

# Load environment variables from the .env file at the root
load_dotenv(ROOT_DIR / ".env")


def load_config(filename: str = "config.yaml") -> dict:
    """Load the YAML configuration file from the project root."""
    config_path = ROOT_DIR / filename
    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found at {config_path}. "
            f"Please copy 'config.example.yaml' to 'config.yaml'."
        )

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config


# Expose a ready-to-use config dictionary and environment helper
config = load_config()


def get_env(key: str, default: str | None = None) -> str:
    """Helper to safely retrieve environment variables."""
    value = os.getenv(key, default)
    if value is None:
        raise ValueError(f"Environment variable '{key}' is not set.")
    return value
