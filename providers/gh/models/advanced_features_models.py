"""Pydantic models for GitHub advanced features data structures."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class TagData(BaseModel):
    """Repository tag information."""
    name: str
    commit_sha: str
    commit_date: Optional[datetime] = None


class WebhookData(BaseModel):
    """Repository webhook information."""
    id: int
    name: str
    active: bool = True
    events: List[str] = Field(default_factory=list)
    config: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AdvancedFeaturesData(BaseModel):
    """Complete advanced features data for a repository."""
    repository: str
    tags: List[TagData] = Field(default_factory=list)
    webhooks: List[WebhookData] = Field(default_factory=list)
    
    # Summary statistics
    total_tags: int = 0
    total_webhooks: int = 0
    active_webhooks: int = 0
    
    # Error tracking
    tags_error: Optional[str] = None
    webhooks_error: Optional[str] = None
    
    def __init__(self, **data):
        super().__init__(**data)
        # Calculate derived fields
        self.total_tags = len(self.tags)
        self.total_webhooks = len(self.webhooks)
        self.active_webhooks = sum(1 for w in self.webhooks if w.active) 