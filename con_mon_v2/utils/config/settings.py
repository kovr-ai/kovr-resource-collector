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
        
        # AWS Configuration
        AWS_REGION (str): AWS region for services, defaults to "us-east-1"
        AWS_PROFILE (str): AWS profile name for credentials, defaults to "dev-kovr"
        AWS_ACCESS_KEY_ID (str): AWS access key ID (optional if using IAM roles)
        AWS_SECRET_ACCESS_KEY (str): AWS secret access key (optional if using IAM roles)
        
        # AWS Bedrock Configuration
        BEDROCK_REGION (str): AWS region for Bedrock service, defaults to "us-east-1"
        BEDROCK_MODEL_ID (str): Bedrock model identifier, defaults to "anthropic.claude-3-sonnet-20240229-v1:0"
        BEDROCK_MAX_TOKENS (int): Maximum tokens for Bedrock responses, defaults to 4096
        BEDROCK_TEMPERATURE (float): Temperature for Bedrock responses, defaults to 0.1
        BEDROCK_TOP_P (float): Top-p sampling for Bedrock responses, defaults to 0.9
        BEDROCK_TIMEOUT (int): Request timeout in seconds, defaults to 300
    """
    
    # Database Configuration
    DB_HOST: str
    DB_PORT: int = 5432
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str

    # CSV Configuration
    CSV_DATA: str
    LOG_LEVEL: str = "DEBUG"
    
    # AWS Configuration
    AWS_REGION: str = "us-east-1"
    AWS_PROFILE: str = "dev-kovr"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    
    # AWS Bedrock Configuration
    BEDROCK_REGION: str = "us-east-1"
    BEDROCK_MODEL_ID: str = "anthropic.claude-3-sonnet-20240229-v1:0"
    BEDROCK_MAX_TOKENS: int = 4096
    BEDROCK_TEMPERATURE: float = 0.1
    BEDROCK_TOP_P: float = 0.9
    BEDROCK_TIMEOUT: int = 300
