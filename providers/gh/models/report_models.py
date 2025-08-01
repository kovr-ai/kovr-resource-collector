"""Main GitHub report Pydantic model."""

from datetime import datetime, timezone
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from .base_models import RepositoriesData
from .actions_models import ActionsData
from .collaboration_models import CollaborationData
from .security_models import SecurityData
from .organization_models import OrganizationData
from .advanced_features_models import AdvancedFeaturesData


class GitHubReport(BaseModel):
    """Complete GitHub data collection report."""
    
    # Metadata
    collection_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    authenticated_user: Optional[str] = None
    total_repositories: int = 0
    
    # Service data per repository
    repositories_data: List[RepositoriesData] = Field(default_factory=list)
    actions_data: List[ActionsData] = Field(default_factory=list)
    collaboration_data: List[CollaborationData] = Field(default_factory=list)
    security_data: List[SecurityData] = Field(default_factory=list)
    organization_data: List[OrganizationData] = Field(default_factory=list)
    advanced_features_data: List[AdvancedFeaturesData] = Field(default_factory=list)
    
    # Rate limit information
    rate_limit_info: Dict = Field(default_factory=dict)
    
    # Overall statistics (calculated automatically)
    total_workflows: int = 0
    total_issues: int = 0
    total_pull_requests: int = 0
    total_security_alerts: int = 0
    total_collaborators: int = 0
    total_tags: int = 0
    total_active_webhooks: int = 0
    
    def __init__(self, **data):
        super().__init__(**data)
        self._calculate_statistics()
    
    def _calculate_statistics(self):
        """Calculate overall statistics from all service data."""
        self.total_repositories = len(self.repositories_data)
        
        # Actions statistics
        self.total_workflows = sum(actions.total_workflows for actions in self.actions_data)
        
        # Collaboration statistics
        self.total_issues = sum(collab.total_issues for collab in self.collaboration_data)
        self.total_pull_requests = sum(collab.total_pull_requests for collab in self.collaboration_data)
        self.total_collaborators = sum(collab.total_collaborators for collab in self.collaboration_data)
        
        # Security statistics
        self.total_security_alerts = sum(
            security.total_advisories + 
            security.total_dependabot_alerts + 
            security.total_code_scanning_alerts
            for security in self.security_data
        )
        
        # Advanced features statistics
        self.total_tags = sum(features.total_tags for features in self.advanced_features_data)
        self.total_active_webhooks = sum(features.active_webhooks for features in self.advanced_features_data)
    
    def add_repository_data(self, repo_data: RepositoriesData):
        """Add repository data to the report."""
        self.repositories_data.append(repo_data)
        self._calculate_statistics()
    
    def add_actions_data(self, actions_data: ActionsData):
        """Add actions data to the report."""
        self.actions_data.append(actions_data)
        self._calculate_statistics()
    
    def add_collaboration_data(self, collaboration_data: CollaborationData):
        """Add collaboration data to the report."""
        self.collaboration_data.append(collaboration_data)
        self._calculate_statistics()
    
    def add_security_data(self, security_data: SecurityData):
        """Add security data to the report."""
        self.security_data.append(security_data)
        self._calculate_statistics()
    
    def add_organization_data(self, organization_data: OrganizationData):
        """Add organization data to the report."""
        self.organization_data.append(organization_data)
        self._calculate_statistics()
    
    def add_advanced_features_data(self, advanced_features_data: AdvancedFeaturesData):
        """Add advanced features data to the report."""
        self.advanced_features_data.append(advanced_features_data)
        self._calculate_statistics()
    
    def get_summary(self) -> Dict:
        """Get a summary of the collected data."""
        return {
            "collection_time": self.collection_time.isoformat(),
            "authenticated_user": self.authenticated_user,
            "statistics": {
                "total_repositories": self.total_repositories,
                "total_workflows": self.total_workflows,
                "total_issues": self.total_issues,
                "total_pull_requests": self.total_pull_requests,
                "total_security_alerts": self.total_security_alerts,
                "total_collaborators": self.total_collaborators,
                "total_tags": self.total_tags,
                "total_active_webhooks": self.total_active_webhooks
            },
            "services_data": {
                "repositories": len(self.repositories_data),
                "actions": len(self.actions_data),
                "collaboration": len(self.collaboration_data),
                "security": len(self.security_data),
                "organization": len(self.organization_data),
                "advanced_features": len(self.advanced_features_data)
            }
        } 