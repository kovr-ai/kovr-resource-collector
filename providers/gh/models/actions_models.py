"""Pydantic models for GitHub Actions/CI-CD data structures."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class WorkflowRun(BaseModel):
    """Individual workflow run data."""
    id: int
    name: str
    head_branch: Optional[str] = None
    head_sha: str
    status: str
    conclusion: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    run_number: int = 0
    run_attempt: int = 1


class WorkflowData(BaseModel):
    """GitHub Actions workflow information."""
    id: int
    name: str
    path: str
    state: str
    created_at: datetime
    updated_at: datetime
    badge_url: str
    recent_runs: List[WorkflowRun] = Field(default_factory=list)


class ActionsData(BaseModel):
    """Complete GitHub Actions data for a repository."""
    repository: str
    workflows: Dict[str, WorkflowData] = Field(default_factory=dict)
    total_workflows: int = 0
    active_workflows: int = 0
    recent_runs_count: int = 0
    
    def __init__(self, **data):
        super().__init__(**data)
        # Calculate derived fields
        self.total_workflows = len(self.workflows)
        self.active_workflows = sum(1 for w in self.workflows.values() if w.state == "active")
        self.recent_runs_count = sum(len(w.recent_runs) for w in self.workflows.values()) 