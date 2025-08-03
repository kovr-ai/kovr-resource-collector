"""
Configuration Management Module

This module provides centralized configuration management for the application,
integrating with AWS Secrets Manager for secure storage and retrieval of settings.
It implements a type-safe settings system using Pydantic models.

Key Features:
- Type-safe configuration using Pydantic models
- Environment-based settings (local, dev, test, prod)
- Integration with AWS Secrets Manager
- Default values for all settings
- Environment variable overrides

Example:
    >>> from con_mon.utils.config import load_settings
    >>> # Load settings for an application
    >>> settings = load_settings(app='con_mon', env='dev')
    >>> # Access settings with type safety
    >>> db_host = settings.DB_HOST
    >>> db_port = settings.DB_PORT
"""

import os
from typing import Dict, Any
from .settings import Settings
from dotenv import load_dotenv

load_dotenv()


def load_settings(app: str = "con_mon", env: str = "local") -> Settings:
    """
    Load application settings from AWS Secrets Manager with type safety.
    Combines environment variables, AWS Secrets Manager values, and default values.

    Args:
        app (str): Application name. Defaults to 'con_mon'
        env (str): Environment name. Defaults to 'local'

    Returns:
        Settings: A Pydantic model containing all application settings with
            proper type validation and default values.

    Example:
        >>> settings = load_settings(app='con_mon', env='dev')
        >>> print(settings.DB_HOST)  # Type-safe access
        'localhost'
        >>> print(settings.DB_PORT)  # Default value if not set
        5432
    """
    # Get app and env from environment variables or use defaults

    load_dotenv()
    secrets = dict()

    # Create settings dictionary with values from secret or defaults
    settings_dict: Dict[str, Any] = {}
    for field_name, field_info in Settings.model_fields.items():
        settings_dict[field_name] = secrets.get(field_name, None) or os.getenv(field_name, field_info.default)

    # Create and return Settings object
    return Settings(**settings_dict)


settings = load_settings()

__all__ = ["settings"]
