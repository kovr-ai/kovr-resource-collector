"""
Models for connectors module - handles data fetching and resource collection.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable
from pydantic import BaseModel, Field
from enum import Enum
from con_mon.resources.models import ResourceCollection


class ConnectorType(Enum):
    """Types of connectors supported."""
    AWS = "aws"
    AZURE = "azure"
    GITHUB = "github"
    GOOGLE = "google"
    KUBERNETES = "kubernetes"
    DOCKER = "docker"
    CUSTOM = "custom"


class ConnectorInput(BaseModel, ABC):
    """Abstract base class for connector input configuration."""
    pass


class ConnectorService(BaseModel):
    """
    Service that contains the python function to fetch data.
    """
    name: str
    description: str
    connector_type: ConnectorType
    fetch_function: Callable[[ConnectorInput], ResourceCollection] = Field(exclude=True)
    
    class Config:
        arbitrary_types_allowed = True

    def fetch_data(self, input_config: ConnectorInput) -> ResourceCollection:
        """
        Fetch data using the configured function.
        
        Args:
            input_config: Input configuration for the connector
            
        Returns:
            ConnectorOutput: The fetched data
        """
        return self.fetch_function(input_config)
