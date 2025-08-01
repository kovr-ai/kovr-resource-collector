"""Pydantic models for GitHub organization data structures."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class OrganizationMemberData(BaseModel):
    """Organization member information."""
    login: str
    id: int
    type: str = "User"
    site_admin: bool = False
    role: Optional[str] = None


class OrganizationTeamData(BaseModel):
    """Organization team information."""
    id: int
    name: str
    slug: str 
    description: Optional[str] = None
    privacy: str = "closed"
    permission: str = "pull"
    members_count: int = 0
    repos_count: int = 0


class OrganizationData(BaseModel):
    """Complete organization data for a repository."""
    repository: str
    members: List[OrganizationMemberData] = Field(default_factory=list)
    teams: List[OrganizationTeamData] = Field(default_factory=list)
    outside_collaborators: List[OrganizationMemberData] = Field(default_factory=list)
    
    # Summary statistics
    total_members: int = 0
    total_teams: int = 0
    total_outside_collaborators: int = 0
    admin_members: int = 0
    
    # Error tracking
    members_error: Optional[str] = None
    teams_error: Optional[str] = None
    collaborators_error: Optional[str] = None
    
    def __init__(self, **data):
        super().__init__(**data)
        # Calculate derived fields
        self.total_members = len(self.members)
        self.total_teams = len(self.teams)
        self.total_outside_collaborators = len(self.outside_collaborators)
        self.admin_members = sum(1 for m in self.members if m.role == "admin") 