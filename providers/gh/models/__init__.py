"""GitHub Provider Pydantic Models

This module contains all the Pydantic models used by the GitHub provider
to structure and validate the collected data.
"""

from .base_models import (
    RepositoryBasicInfo,
    RepositoryMetadata,
    BranchData,
    StatisticsData,
    RepositoriesData
)

from .actions_models import (
    WorkflowRun,
    WorkflowData,
    ActionsData
)

from .collaboration_models import (
    IssueData,
    PullRequestData,
    CollaboratorData,
    CollaborationData
)

from .security_models import (
    SecurityAdvisoryData,
    VulnerabilityAlertData,
    DependencyGraphData,
    SecurityAnalysisData,
    CodeScanningAlertData,
    SecurityData
)

from .organization_models import (
    OrganizationMemberData,
    OrganizationTeamData,
    OrganizationData
)

from .advanced_features_models import (
    TagData,
    WebhookData,
    AdvancedFeaturesData
)

from .report_models import (
    GitHubReport
)

__all__ = [
    # Base models
    "RepositoryBasicInfo",
    "RepositoryMetadata", 
    "BranchData",
    "StatisticsData",
    "RepositoriesData",
    
    # Service models
    "WorkflowRun",
    "WorkflowData", 
    "ActionsData",
    "IssueData",
    "PullRequestData",
    "CollaboratorData",
    "CollaborationData",
    "SecurityAdvisoryData",
    "VulnerabilityAlertData",
    "DependencyGraphData", 
    "SecurityAnalysisData",
    "CodeScanningAlertData",
    "SecurityData",
    "OrganizationMemberData",
    "OrganizationTeamData",
    "OrganizationData",
    "TagData",
    "WebhookData",
    "AdvancedFeaturesData",
    
    # Report model
    "GitHubReport"
] 