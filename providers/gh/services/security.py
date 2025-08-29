from providers.service import BaseService, service_class
from github import Github
from github.Repository import Repository
from ..models.security_models import (
    SecurityAdvisoryData,
    DependabotAlertData,
    VulnerabilityAlertData,
    DependencyGraphData,
    SecurityAnalysisData,
    CodeScanningData,
    SecurityData
)

@service_class
class SecurityService(BaseService):
    def __init__(self, client: Github, repository: Repository):
        super().__init__(client)
        self.repo = repository

    def process(self) -> SecurityData:
        """Collect security-related data and return SecurityData model"""
        # Initialize with default values
        security_advisories = {}
        vulnerability_alerts = VulnerabilityAlertData()
        dependency_graph = DependencyGraphData()
        security_analysis = SecurityAnalysisData()
        code_scanning_alerts = {}
        
        # Collect each type of security data individually
        try:
            security_advisories = self._collect_security_advisories()
        except Exception as e:
            print(f"Failed to collect security_advisories for {self.repo.name}: {e}")
            security_advisories = {"error": str(e)}
            
        try:
            vulnerability_alerts = self._collect_vulnerability_alerts()
        except Exception as e:
            print(f"Failed to collect vulnerability_alerts for {self.repo.name}: {e}")
            vulnerability_alerts = VulnerabilityAlertData(error=str(e))
            
        try:
            dependency_graph = self._collect_dependency_graph()
        except Exception as e:
            print(f"Failed to collect dependency_graph for {self.repo.name}: {e}")
            dependency_graph = DependencyGraphData()
            
        try:
            security_analysis = self._collect_security_analysis()
        except Exception as e:
            print(f"Failed to collect security_analysis for {self.repo.name}: {e}")
            security_analysis = SecurityAnalysisData()
            
        try:
            code_scanning_alerts = self._collect_code_scanning_alerts()
        except Exception as e:
            print(f"Failed to collect code_scanning_alerts for {self.repo.name}: {e}")
            code_scanning_alerts = {"error": str(e)}
            
        return SecurityData(
            repository=self.repo.full_name,
            security_advisories=security_advisories,
            vulnerability_alerts=vulnerability_alerts,
            dependency_graph=dependency_graph,
            security_analysis=security_analysis,
            code_scanning_alerts=code_scanning_alerts
        )

    def _collect_security_advisories(self):
        """Collect security advisories"""
        try:
            advisories = {}
            # Use the correct PyGithub method for repository security advisories
            advisories_list = list(self.repo.get_repository_advisories())
            for advisory in advisories_list:
                advisory_data = SecurityAdvisoryData(
                    ghsa_id=advisory.ghsa_id,
                    summary=advisory.summary,
                    description=advisory.description,
                    severity=advisory.severity,
                    state=advisory.state,
                    published_at=advisory.published_at,
                    updated_at=advisory.updated_at
                )
                advisories[advisory.ghsa_id] = advisory_data
            return advisories
                
        except Exception as e:
            print(f"Could not access repository advisories (may require permissions): {e}")
            raise e

    def _collect_vulnerability_alerts(self) -> VulnerabilityAlertData:
        """Collect vulnerability alert status"""
        try:
            # Check if vulnerability alerts are enabled
            alert_status = self.repo.get_vulnerability_alert()
            
            # Get Dependabot alerts if available
            dependabot_alerts = []
            try:
                alerts_list = list(self.repo.get_dependabot_alerts())[:20]  # Limit to prevent overload
                for alert in alerts_list:
                    alert_data = DependabotAlertData(
                        number=alert.number,
                        state=alert.state,
                        severity=alert.security_advisory.severity,
                        package=alert.dependency.package.name,
                        created_at=alert.created_at,
                        updated_at=alert.updated_at
                    )
                    dependabot_alerts.append(alert_data)
                    
            except Exception as e:
                print(f"Could not get Dependabot alerts: {e}")
                
            return VulnerabilityAlertData(
                enabled=alert_status,
                dependabot_alerts=dependabot_alerts
            )
                
        except Exception as e:
            print(f"Could not access vulnerability alerts (may require permissions): {e}")
            raise e

    def _collect_dependency_graph(self) -> DependencyGraphData:
        """Collect dependency graph information"""
        try:
            # Try to get some dependency information safely
            security_and_analysis = {}
            
            # Safe access to security_and_analysis
            if hasattr(self.repo, 'security_and_analysis') and self.repo.security_and_analysis:
                sec_analysis = self.repo.security_and_analysis
                security_and_analysis = {
                    "advanced_security": str(getattr(sec_analysis, 'advanced_security', None)),
                    "secret_scanning": str(getattr(sec_analysis, 'secret_scanning', None)),
                    "secret_scanning_push_protection": str(getattr(sec_analysis, 'secret_scanning_push_protection', None))
                }
            else:
                security_and_analysis = {"info": "Security and analysis settings not available"}
                
            return DependencyGraphData(
                has_vulnerability_alerts_enabled=getattr(self.repo, 'has_vulnerability_alerts_enabled', None),
                security_and_analysis=security_and_analysis
            )
                
        except Exception as e:
            print(f"Could not access dependency information: {e}")
            raise e
    
    def _collect_security_analysis(self) -> SecurityAnalysisData:
        """Collect security analysis configuration"""
        try:
            # Try to get actual security settings with safe attribute access
            advanced_security_enabled = False
            secret_scanning_enabled = False
            push_protection_enabled = False
            dependency_review_enabled = False
            
            if hasattr(self.repo, 'security_and_analysis') and self.repo.security_and_analysis:
                sec_analysis = self.repo.security_and_analysis
                
                # Safe access to nested attributes
                adv_security = getattr(sec_analysis, 'advanced_security', None)
                if adv_security and hasattr(adv_security, 'status'):
                    advanced_security_enabled = adv_security.status == 'enabled'
                
                secret_scan = getattr(sec_analysis, 'secret_scanning', None)
                if secret_scan and hasattr(secret_scan, 'status'):
                    secret_scanning_enabled = secret_scan.status == 'enabled'
                
                push_protection = getattr(sec_analysis, 'secret_scanning_push_protection', None)
                if push_protection and hasattr(push_protection, 'status'):
                    push_protection_enabled = push_protection.status == 'enabled'
                        
            return SecurityAnalysisData(
                advanced_security_enabled=advanced_security_enabled,
                secret_scanning_enabled=secret_scanning_enabled,
                push_protection_enabled=push_protection_enabled,
                dependency_review_enabled=dependency_review_enabled
            )
                
        except Exception as e:
            print(f"Could not access security analysis settings: {e}")
            raise e
    
    def _collect_code_scanning_alerts(self):
        """Collect code scanning alerts"""
        try:
            # Use the correct PyGithub method for code scanning alerts
            scanning_alerts = []
            alerts_list = list(self.repo.get_codescan_alerts())[:20]  # Limit to prevent overload
            for alert in alerts_list:
                alert_data = {
                    "number": alert.number,
                    "state": alert.state,
                    "rule_id": alert.rule.id,
                    "rule_severity": alert.rule.severity,
                    "tool_name": alert.tool.name,
                    "created_at": alert.created_at,
                    "updated_at": alert.updated_at
                }
                scanning_alerts.append(alert_data)
                
            return CodeScanningData(code_scanning_alerts=scanning_alerts)
            
        except Exception as e:
            print(f"Could not access code scanning alerts (may require permissions): {e}")
            raise e 