"""
Application settings loaded from .env and YAML config files.
"""

import os
import yaml
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

# Project root is two levels up from this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIGS_DIR = PROJECT_ROOT / "configs"
DATA_DIR = PROJECT_ROOT / "data"


class Settings(BaseSettings):
    """App settings from environment variables."""
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "phi3:mini"
    llm_provider: str = "gemini"
    gemini_api_key: str | None = None
    sarvam_api_key: str | None = None
    db_path: str = str(DATA_DIR / "app.db")
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    allowed_origins: list[str] = ["http://localhost:8501"]
    instagram_username: str | None = None
    instagram_password: str | None = None

    class Config:
        env_file = str(PROJECT_ROOT / ".env")
        extra = "ignore"


settings = Settings()


def load_yaml_config(filename: str) -> dict:
    """Load a YAML config file from the configs directory."""
    filepath = CONFIGS_DIR / filename
    with open(filepath, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_sources_allowlist() -> dict:
    return load_yaml_config("sources_allowlist.yaml")


def get_instagram_allowlist() -> dict:
    return load_yaml_config("instagram_allowlist.yaml")


def get_topics() -> list[str]:
    data = load_yaml_config("topics.yaml")
    return data.get("topics", [])


def get_specialist_map() -> dict:
    return load_yaml_config("specialist_map.yaml")


def get_triage_rules() -> dict:
    return load_yaml_config("triage_rules.yaml")


def load_prompt(filename: str) -> str:
    """Load a prompt template from configs/prompts/."""
    filepath = CONFIGS_DIR / "prompts" / filename
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()
