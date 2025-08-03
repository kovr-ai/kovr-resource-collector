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
from typing import Dict, Any
from resources import GithubResourceCollection

# Load environment variables from .env file
load_dotenv()


@provider_class
class GitHubProvider(Provider):
    def __init__(self, metadata: dict):
        self.config = self.load_config("providers/gh/github_config.json")
        self.output_dir = Path("output/github")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.metadata = self.prepare_metadata()
        self.GITHUB_TOKEN = self.metadata["GITHUB_TOKEN"]

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

    def load_config(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                print(f"Loaded configuration from {config_file}")
                return config
        except FileNotFoundError:
            print(f"Configuration file {config_file} not found. Using default settings.")
            return {
                "github": {
                    "output_config": {
                        "repositories": True,
                        "actions": True,
                        "collaboration": True,
                        "security": True,
                        "organization": True,
                        "advanced_features": True
                    }
                },
                "features": {
                    "rate_limit_monitoring": True,
                    "detailed_logging": True
                }
            }
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return {}

    def prepare_metadata(self) -> Dict[str, Any]:
        """Prepare metadata for the GitHub provider"""
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            raise ValueError("GITHUB_TOKEN environment variable is required")
        
        return {
            "GITHUB_TOKEN": github_token,
            "config": self.config,
            "output_dir": str(self.output_dir)
        }

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
            self.user = self.client.get_user()
            print(f"Connected to GitHub as: {self.user.login}")
        except GithubException as e:
            print(f"GitHub connection error: {e}")
            raise
        except Exception as e:
            print(f"Unexpected error during GitHub connection: {e}")
            raise

    # def process(self) -> GitHubReport:
    def process(self) -> GithubResourceCollection:
        """Process data collection and return GitHubReport model"""
        # Create the report object
        with open(
            '/Users/ironeagle-kovr/Workspace/code/kovr-resource-collector/2025-08-02-19-03-26_response.json',
            'r'
        ) as mock_response_file:
            mock_response = json.load(mock_response_file)
            
            # Import the resource models
            from resources import GithubResourceCollection, GithubResource
            
            # Convert repositories_data to GithubResource objects
            github_resources = []
            for repo_data in mock_response.get('repositories_data', []):
                try:
                    # Add required base Resource fields
                    repo_data_with_base_fields = {
                        **repo_data,
                        'id': f"github-{repo_data.get('repository', 'unknown').replace('/', '-')}",
                        'source_connector': 'github'
                    }
                    
                    github_resource = GithubResource(**repo_data_with_base_fields)
                    github_resources.append(github_resource)
                except Exception as e:
                    print(f"Error converting repository data: {e}")
                    continue
            
            # Create and return GithubResourceCollection
            return GithubResourceCollection(resources=github_resources)

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
