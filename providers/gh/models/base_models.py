"""Base Pydantic models for GitHub provider data structures."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class RepositoryBasicInfo(BaseModel):
    """Basic information about a GitHub repository."""
    id: int
    name: str
    full_name: str
    description: Optional[str] = None
    private: bool
    owner: str
    html_url: str
    clone_url: str
    ssh_url: str
    size: int
    language: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    pushed_at: Optional[datetime] = None
    stargazers_count: int = 0
    watchers_count: int = 0
    forks_count: int = 0
    open_issues_count: int = 0
    archived: bool = False
    disabled: bool = False


class RepositoryMetadata(BaseModel):
    """Extended metadata for a repository."""
    default_branch: str
    topics: List[str] = Field(default_factory=list)
    has_issues: bool = True
    has_projects: bool = True
    has_wiki: bool = True
    has_pages: bool = False
    has_downloads: bool = True
    has_discussions: bool = False
    is_template: bool = False
    license: Optional[Dict[str, Any]] = None


class BranchData(BaseModel):
    """Information about repository branches."""
    name: str
    sha: str
    protected: bool = False
    protection_details: Optional[Dict[str, Any]] = None


class StatisticsData(BaseModel):
    """Repository statistics and metrics."""
    total_commits: int = 0
    contributors_count: int = 0
    languages: Dict[str, int] = Field(default_factory=dict)
    code_frequency: List[Dict[str, Any]] = Field(default_factory=list)


class RepositoriesData(BaseModel):
    """Complete repository data structure."""
    repository: str
    basic_info: RepositoryBasicInfo
    metadata: RepositoryMetadata
    branches: List[BranchData] = Field(default_factory=list)
    statistics: StatisticsData 