"""Pydantic models for GitHub collaboration data structures."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class IssueData(BaseModel):
    """Individual issue data."""
    number: int
    title: str
    state: str
    user: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    labels: List[str] = Field(default_factory=list)
    assignees: List[str] = Field(default_factory=list)
    comments_count: int = 0
    is_pull_request: bool = False


class PullRequestData(BaseModel):
    """Individual pull request data."""
    number: int
    title: str
    state: str
    user: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    merged_at: Optional[datetime] = None
    base_branch: str
    head_branch: str
    draft: bool = False
    mergeable: Optional[bool] = None
    additions: int = 0
    deletions: int = 0
    changed_files: int = 0
    commits: int = 0
    comments: int = 0
    review_comments: int = 0


class CollaboratorData(BaseModel):
    """Repository collaborator information."""
    login: str
    permissions: Dict[str, bool] = Field(default_factory=dict)
    role_name: Optional[str] = None


class CollaborationData(BaseModel):
    """Complete collaboration data for a repository."""
    repository: str
    issues: List[IssueData] = Field(default_factory=list)
    pull_requests: List[PullRequestData] = Field(default_factory=list)
    collaborators: List[CollaboratorData] = Field(default_factory=list)
    
    # Summary statistics
    total_issues: int = 0
    open_issues: int = 0
    closed_issues: int = 0
    total_pull_requests: int = 0
    open_pull_requests: int = 0
    merged_pull_requests: int = 0
    draft_pull_requests: int = 0
    total_collaborators: int = 0
    
    def __init__(self, **data):
        super().__init__(**data)
        # Calculate derived fields
        self.total_issues = len(self.issues)
        self.open_issues = sum(1 for i in self.issues if i.state == "open")
        self.closed_issues = sum(1 for i in self.issues if i.state == "closed")
        
        self.total_pull_requests = len(self.pull_requests)
        self.open_pull_requests = sum(1 for pr in self.pull_requests if pr.state == "open")
        self.merged_pull_requests = sum(1 for pr in self.pull_requests if pr.merged_at is not None)
        self.draft_pull_requests = sum(1 for pr in self.pull_requests if pr.draft)
        
        self.total_collaborators = len(self.collaborators) 