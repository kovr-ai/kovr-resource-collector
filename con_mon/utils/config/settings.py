"""
Settings Model

This module defines the application's configuration settings using Pydantic models.
It provides type-safe configuration management with default values and validation.

The Settings model includes all configuration parameters needed by the application,
including database connections, AWS services, LLM providers, and application-specific settings.
"""

from pydantic import BaseModel, Field


class Settings(BaseModel):
    """
    Application settings model with type-safe configuration and default values.
    
    This model defines all configuration parameters used throughout the application,
    with appropriate types and default values where applicable.
    
    Attributes:
        DB_HOST (str): Database host address
        DB_PORT (int): Database port number, defaults to 5432
        DB_NAME (str): Database name
        DB_USER (str): Database username
        DB_PASSWORD (str): Database password
        LOG_LEVEL (str): Application log level, defaults to "DEBUG"
    """
    
    # Database Configuration
    DB_HOST: str
    DB_PORT: int = 5432
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    LOG_LEVEL: str = "DEBUG"
