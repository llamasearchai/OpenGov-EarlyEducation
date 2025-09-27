#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration management for OpenEarlyEducation.

Handles environment variables, configuration files, and provides
a clean interface for application settings.
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from openai import OpenAI


@dataclass
class Config:
    """Configuration settings for OpenEarlyEducation."""

    # OpenAI settings
    openai_api_key: str
    openai_model: str = "gpt-4o"
    openai_max_tokens: int = 4096
    openai_temperature: float = 0.7

    # Database settings
    database_path: str = "open_early_education.db"

    # Application settings
    assistant_cache_path: str = ".open_early_education_assistant.json"
    log_level: str = "INFO"
    max_retries: int = 3
    retry_delay: float = 1.0

    # Server settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Feature flags
    enable_pdf_export: bool = True
    enable_docker_support: bool = False

    @property
    def openai_client(self) -> OpenAI:
        """Get OpenAI client instance."""
        return OpenAI(api_key=self.openai_api_key)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """Create config from dictionary."""
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "openai_api_key": self.openai_api_key,
            "openai_model": self.openai_model,
            "openai_max_tokens": self.openai_max_tokens,
            "openai_temperature": self.openai_temperature,
            "database_path": self.database_path,
            "assistant_cache_path": self.assistant_cache_path,
            "log_level": self.log_level,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "api_host": self.api_host,
            "api_port": self.api_port,
            "enable_pdf_export": self.enable_pdf_export,
            "enable_docker_support": self.enable_docker_support,
        }


def get_config(config_path: Optional[str] = None) -> Config:
    """Get configuration from environment and optional config file."""

    # Start with default values
    config_data = {
        "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
        "openai_model": os.getenv("OPENAI_MODEL", "gpt-4o"),
        "openai_max_tokens": int(os.getenv("OPENAI_MAX_TOKENS", "4096")),
        "openai_temperature": float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
        "database_path": os.getenv("DATABASE_PATH", "open_early_education.db"),
        "assistant_cache_path": os.getenv(
            "ASSISTANT_CACHE_PATH", ".open_early_education_assistant.json"
        ),
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "max_retries": int(os.getenv("MAX_RETRIES", "3")),
        "retry_delay": float(os.getenv("RETRY_DELAY", "1.0")),
        "api_host": os.getenv("API_HOST", "0.0.0.0"),
        "api_port": int(os.getenv("API_PORT", "8000")),
        "enable_pdf_export": os.getenv("ENABLE_PDF_EXPORT", "true").lower() == "true",
        "enable_docker_support": os.getenv("ENABLE_DOCKER_SUPPORT", "false").lower() == "true",
    }

    # Load from config file if provided
    if config_path:
        config_file = Path(config_path)
        if config_file.exists():
            try:
                file_data = json.loads(config_file.read_text(encoding="utf-8"))
                config_data.update(file_data)
            except Exception as e:
                raise ValueError(f"Error loading config file {config_path}: {e}")

    # Validate required fields
    if not config_data["openai_api_key"]:
        # Allow empty in testing contexts
        if os.getenv("PYTEST_CURRENT_TEST"):
            config_data["openai_api_key"] = "test_key"
        else:
            raise ValueError("OPENAI_API_KEY environment variable is required")

    return Config.from_dict(config_data)


def save_config(config: Config, config_path: str) -> None:
    """Save configuration to file."""
    config_file = Path(config_path)
    config_file.parent.mkdir(parents=True, exist_ok=True)

    # Don't save API key to file for security
    save_data = config.to_dict()
    save_data.pop("openai_api_key", None)

    config_file.write_text(json.dumps(save_data, indent=2), encoding="utf-8")


def create_default_config() -> Config:
    """Create a default configuration."""
    return Config(
        openai_api_key="",  # Must be set via environment
        openai_model="gpt-4o",
        openai_max_tokens=4096,
        openai_temperature=0.7,
        database_path="open_early_education.db",
        assistant_cache_path=".open_early_education_assistant.json",
        log_level="INFO",
        max_retries=3,
        retry_delay=1.0,
        api_host="0.0.0.0",
        api_port=8000,
        enable_pdf_export=True,
        enable_docker_support=False,
    )
