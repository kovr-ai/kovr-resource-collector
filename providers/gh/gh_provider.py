from providers.provider import Provider, provider_class
from constants import Providers
import os
import importlib
from github import Github, Auth
from github.GithubException import GithubException
from .models.report_models import GitHubReport
from dotenv import load_dotenv
from pathlib import Path
import json
from typing import Dict, Any, Tuple
from con_mon.resources import GithubInfoData, GithubResource, GithubResourceCollection

# Load environment variables from .env file
load_dotenv()


@provider_class
class GitHubProvider(Provider):
    def __init__(self, metadata: dict):
        self.GITHUB_TOKEN = metadata["personal_access_token"]

        super().__init__(Providers.GITHUB.value, metadata)
        
        # Define services to collect data from
        self.services = [
            {"name": "repositories", "class": self._get_service_class("RepositoriesService")},
            {"name": "actions", "class": self._get_service_class("ActionsService")},  
            {"name": "collaboration", "class": self._get_service_class("CollaborationService")},
            {"name": "security", "class": self._get_service_class("SecurityService")},
            {"name": "organization", "class": self._get_service_class("OrganizationService")},
            {"name": "advanced_features", "class": self._get_service_class("AdvancedFeaturesService")}
        ]

    def _get_service_class(self, service_class_name: str):
        """Dynamically load and return service class"""
        try:
            # Map service class names to their module names
            service_module_map = {
                "RepositoriesService": "repositories",
                "ActionsService": "actions", 
                "CollaborationService": "collaboration",
                "SecurityService": "security",
                "OrganizationService": "organization",
                "AdvancedFeaturesService": "advanced_features"
            }
            
            if service_class_name not in service_module_map:
                raise ValueError(f"Unknown service class: {service_class_name}")
            
            module_name = service_module_map[service_class_name]
            module_path = f"providers.gh.services.{module_name}"
            
            # Import the module
            module = importlib.import_module(module_path)
            
            # Get the service class
            service_class = getattr(module, service_class_name)
            return service_class
            
        except Exception as e:
            print(f"Error loading service class {service_class_name}: {e}")
            raise

    def connect(self):
        """Establish connection to GitHub API"""
        try:
            auth = Auth.Token(self.GITHUB_TOKEN)
            self.client = Github(auth=auth)
            # self.user = self.client.get_user()
            # print(f"Connected to GitHub as: {self.user.login}")
        except GithubException as e:
            print(f"GitHub connection error: {e}")
            raise
        except Exception as e:
            print(f"Unexpected error during GitHub connection: {e}")
            raise

    def process(self) -> Tuple[GithubInfoData, GithubResourceCollection]:
        """Process data collection and return GitHubReport model"""
        with open(
            'github_response.json',
            'r'
        ) as mock_response_file:
            mock_response = json.load(mock_response_file)
            
            # Create lookup dictionaries for each data type by repository
            repositories_lookup = {item['repository']: item for item in mock_response.get('repositories_data', [])}
            actions_lookup = {item['repository']: item for item in mock_response.get('actions_data', [])}
            collaboration_lookup = {item['repository']: item for item in mock_response.get('collaboration_data', [])}
            security_lookup = {item['repository']: item for item in mock_response.get('security_data', [])}
            organization_lookup = {item['repository']: item for item in mock_response.get('organization_data', [])}
            advanced_features_lookup = {item['repository']: item for item in mock_response.get('advanced_features_data', [])}
            
            # Convert to GithubResource objects with ALL data types
            github_resources = []
            for repo_name in repositories_lookup.keys():
                try:
                    # Create comprehensive GithubResource with all data types
                    resource_data = {
                        'name': repo_name,
                        'repository_data': repositories_lookup.get(repo_name, {}),
                        'actions_data': actions_lookup.get(repo_name, {}),
                        'collaboration_data': collaboration_lookup.get(repo_name, {}),
                        'security_data': security_lookup.get(repo_name, {}),
                        'organization_data': organization_lookup.get(repo_name, {}),
                        'advanced_features_data': advanced_features_lookup.get(repo_name, {}),
                        # Add required base Resource fields
                        'id': f"github-{repo_name.replace('/', '-')}",
                        'source_connector': 'github'
                    }

                    github_resource = GithubResource(**resource_data)
                    github_resources.append(github_resource)
                except Exception as e:
                    print(f"Error converting repository data for {repo_name}: {e}")
                    continue
            
            # Create and return GithubResourceCollection
            resource_collection = GithubResourceCollection(
                resources=github_resources,
                source_connector='github',
                total_count=len(github_resources),
                fetched_at=mock_response.get('collection_time'),
                collection_metadata={
                    'authenticated_user': mock_response.get('authenticated_user'),
                    'total_repositories': mock_response.get('total_repositories'),
                    'total_workflows': mock_response.get('total_workflows', 0),
                    'total_issues': mock_response.get('total_issues', 0),
                    'total_pull_requests': mock_response.get('total_pull_requests', 0),
                    'total_security_alerts': mock_response.get('total_security_alerts', 0),
                    'total_collaborators': mock_response.get('total_collaborators', 0),
                    'total_tags': mock_response.get('total_tags', 0),
                    'total_active_webhooks': mock_response.get('total_active_webhooks', 0),
                    'rate_limit_info': mock_response.get('rate_limit_info')
                },
                github_api_metadata={
                    'collection_time': mock_response.get('collection_time'),
                    'api_version': 'v3',  # GitHub API version
                    'scope': ['repo', 'read:org', 'actions:read', 'security_events:read']  # Extended scopes
                }
            )
            
            # Create InfoData from the resource collection metadata
            info_data = GithubInfoData(
                repositories=[
                    {
                        'name': repo.name,
                        'url': repo.repository_data.basic_info.html_url if hasattr(repo, 'repository_data') and hasattr(repo.repository_data, 'basic_info') else f"https://github.com/{repo.name}",
                        'default_branch_name': repo.repository_data.metadata.default_branch if hasattr(repo, 'repository_data') and hasattr(repo.repository_data, 'metadata') else 'main'
                    }
                    for repo in github_resources
                ]
            )
            
            return info_data, resource_collection

        # Note: The code below is for real GitHub API calls (not currently used)
        # This would need similar updates to return (InfoData, ResourceCollection) tuple
        report = GitHubReport(
            authenticated_user=self.user.login if hasattr(self, 'user') else None
        )
        
        # Get list of repositories
        try:
            repos = list(self.user.get_repos())
            print(f"Found {len(repos)} repositories")
        except Exception as e:
            print(f"Error getting repositories: {e}")
            repos = []
        
        # Process each repository
        for repo in repos:
            print(f"Processing repository: {repo.full_name}")
            
            # Process each service for this repository
            for service in self.services:
                try:
                    print(f"Collecting data for service: {service['name']}")
                    instance = service["class"](self.client, repo)
                    service_data = instance.process()
                    
                    # Add data to report based on service type
                    if service['name'] == 'repositories':
                        report.add_repository_data(service_data)
                    elif service['name'] == 'actions':
                        report.add_actions_data(service_data)
                    elif service['name'] == 'collaboration':
                        report.add_collaboration_data(service_data)
                    elif service['name'] == 'security':
                        report.add_security_data(service_data)
                    elif service['name'] == 'organization':
                        report.add_organization_data(service_data)
                    elif service['name'] == 'advanced_features':
                        report.add_advanced_features_data(service_data)
                        
                except Exception as e:
                    print(f"Error processing {service['name']} for {repo.full_name}: {e}")
                    continue
        
            # MINI RUN: Break after first repository for testing
            print("Mini run complete - stopping after first repository")
            break

        # Add rate limit information
        try:
            rate_limit = self.client.get_rate_limit()
            if rate_limit and hasattr(rate_limit, 'core'):
                report.rate_limit_info = {
                    'core': {
                        'limit': rate_limit.core.limit,
                        'remaining': rate_limit.core.remaining,
                        'reset': rate_limit.core.reset.isoformat()
                    }
                }
        except Exception as e:
            print(f"Could not get rate limit info: {e}")
        
        return report.model_dump()
