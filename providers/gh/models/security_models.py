"""Pydantic models for GitHub security data structures."""

from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field


class SecurityAdvisoryData(BaseModel):
    """Security advisory information."""
    ghsa_id: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None
    state: Optional[str] = None
    published_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    error: Optional[str] = None  # For cases where advisory data couldn't be retrieved


class DependabotAlertData(BaseModel):
    """Individual Dependabot alert."""
    number: int
    state: str
    severity: str
    package: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class VulnerabilityAlertData(BaseModel):
    """Vulnerability alerts status and data."""
    enabled: bool = False
    dependabot_alerts: List[DependabotAlertData] = Field(default_factory=list)
    error: Optional[str] = None


class SecurityAnalysisFeature(BaseModel):
    """Security analysis feature status."""
    status: str = "disabled"


class DependencyGraphData(BaseModel):
    """Dependency graph and security analysis info."""
    has_vulnerability_alerts_enabled: Optional[bool] = None
    security_and_analysis: Dict[str, Union[str, None]] = Field(default_factory=dict)


class SecurityAnalysisData(BaseModel):
    """Security analysis configuration."""
    advanced_security_enabled: bool = False
    secret_scanning_enabled: bool = False
    push_protection_enabled: bool = False
    dependency_review_enabled: bool = False


class CodeScanningAlertData(BaseModel):
    """Code scanning alert information."""
    number: Optional[int] = None
    state: Optional[str] = None
    rule_id: Optional[str] = None
    rule_severity: Optional[str] = None
    tool_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CodeScanningData(BaseModel):
    """Code scanning alerts and configuration."""
    code_scanning_alerts: List[CodeScanningAlertData] = Field(default_factory=list)
    error: Optional[str] = None


class SecurityData(BaseModel):
    """Complete security data for a repository."""
    repository: str
    security_advisories: Union[Dict[str, SecurityAdvisoryData], Dict[str, str]] = Field(default_factory=dict)
    vulnerability_alerts: VulnerabilityAlertData = Field(default_factory=VulnerabilityAlertData)
    dependency_graph: DependencyGraphData = Field(default_factory=DependencyGraphData)
    security_analysis: SecurityAnalysisData = Field(default_factory=SecurityAnalysisData)
    code_scanning_alerts: Union[CodeScanningData, Dict[str, str]] = Field(default_factory=dict)
    
    # Summary statistics
    total_advisories: int = 0
    total_dependabot_alerts: int = 0
    total_code_scanning_alerts: int = 0
    security_features_enabled: int = 0
    
    def __init__(self, **data):
        super().__init__(**data)
        # Calculate derived fields
        if isinstance(self.security_advisories, dict) and "error" not in self.security_advisories:
            self.total_advisories = len(self.security_advisories)
        
        self.total_dependabot_alerts = len(self.vulnerability_alerts.dependabot_alerts)
        
        if isinstance(self.code_scanning_alerts, CodeScanningData):
            self.total_code_scanning_alerts = len(self.code_scanning_alerts.code_scanning_alerts)
        
        # Count enabled security features
        analysis = self.security_analysis
        self.security_features_enabled = sum([
            analysis.advanced_security_enabled,
            analysis.secret_scanning_enabled,
            analysis.push_protection_enabled,
            analysis.dependency_review_enabled
        ]) 