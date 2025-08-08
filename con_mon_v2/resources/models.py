"""
Models for resources module - represents individual data items and collections.
"""
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime


class Resource(BaseModel):
    """
    Represents a single resource item that checks will evaluate.
    This is the fundamental unit that connectors fetch and checks operate on.
    """
    id: str
    source_connector: str


class ResourceCollection(BaseModel):
    """
    Represents a collection of resources, typically the result of a connector's fetch operation.
    """
    resources: List[Resource]
    source_connector: str
    total_count: int
    fetched_at: datetime = Field(default_factory=datetime.now)
    
    def __len__(self) -> int:
        """Return the number of resources in the collection."""
        return len(self.resources)
    
    def __iter__(self):
        """Make the collection iterable."""
        return iter(self.resources)
    
    def __getitem__(self, index: Union[int, slice]) -> Union[Resource, List[Resource]]:
        """Allow indexing and slicing of the collection."""
        return self.resources[index]

    def get_by_id(self, resource_id: str) -> Optional[Resource]:
        """Get a resource by its ID."""
        for resource in self.resources:
            if resource.id == resource_id:
                return resource
        return None
