from providers.provider import Provider, provider_class
from constants import Providers
import os
import importlib
from datetime import datetime
from github import Github, Auth
from github.GithubException import GithubException
from .models.report_models import GitHubReport
from dotenv import load_dotenv
from pathlib import Path
import json
from typing import Dict, Any, Tuple, List
from con_mon.mappings.github import (
    GithubInfoData,
    GithubResource,
    GithubResourceCollection
)


@provider_class
class GitHubProvider(Provider):
    def __init__(self, metadata: dict):
        self._mock_response_filepath = 'tests/mocks/github/response.json'
        self.access_token = metadata["personal_access_token"]
        self.user = None

        super().__init__(Providers.GITHUB.value, metadata)

        # Define services to collect data from
        self.services = [
            {"key": "repository_data", "name": "repositories", "class": self._get_service_class("RepositoriesService")},
            {"key": "actions_data", "name": "actions", "class": self._get_service_class("ActionsService")},
            {"key": "collaboration_data", "name": "collaboration", "class": self._get_service_class("CollaborationService")},
            {"key": "security_data", "name": "security", "class": self._get_service_class("SecurityService")},
            {"key": "organization_data", "name": "organization", "class": self._get_service_class("OrganizationService")},
            {"key": "advanced_features_data", "name": "advanced_features", "class": self._get_service_class("AdvancedFeaturesService")}
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

    def _save_mock_data(self, data: dict) -> None:
        print("🔄 Collecting mock AWS data via test mocks")
        with open(
                self._mock_response_filepath,
                'w'
        ) as mock_response_file:
            mock_response_file.write(json.dumps(data, indent=4))

    def _fetch_data(self) -> dict:
        """Process data collection and return GitHubReport model"""
        try:
            repos = list(self.user.get_repos())
            print(f"Found {len(repos)} repositories")
        except Exception as e:
            print(f"Error getting repositories: {e}")
            repos = []

        data: dict = dict()
        # Process each repository
        for repo in repos:
            repo_id = repo.full_name
            print(f"Processing repository: {repo_id}")
            repo_dict: dict = dict(
                id=repo_id,
                description=repo.description
            )
            # Process each service for this repository
            for service in self.services:
                try:
                    print(f"Collecting data for service: {service['name']}")
                    instance = service["class"](self.client, repo)
                    service_data = instance.process()
                    repo_dict.update({
                        service['key']: json.loads(service_data.model_dump_json())
                    })
                except Exception as e:
                    repo_dict.update({
                        service['key']: dict()
                    })
                    print(f"Error processing {service['name']} for {repo_id}: {e}")
                    continue

            data.update({repo_id: repo_dict})

        return data

    def connect(self):
        """Establish connection to GitHub API"""
        try:
            auth = Auth.Token(self.access_token)
            self.client = Github(auth=auth)
            self.user = self.client.get_user()
            print(f"Connected to GitHub as: {self.user.login}")
        except GithubException as e:
            print(f"GitHub connection error: {e}")
            raise
        except Exception as e:
            print(f"Unexpected error during GitHub connection: {e}")
            raise

    def process(self) -> Tuple[GithubInfoData, GithubResourceCollection]:
        """Process data collection and return GitHubReport model"""
        data: dict = self._fetch_data()
        resource_collection = self._create_resource_collection_from_data(data)
        info_data = self._create_info_data_from_resource_collection(resource_collection)
        return info_data, resource_collection

    def _create_resource_collection_from_data(self, data: dict) -> GithubResourceCollection:
        resource_collection = GithubResourceCollection(
            resources=list(),
            source_connector='github',
            total_count=0,
            fetched_at=datetime.now().isoformat()
        )
        # Process each repository
        for resource_id, resource_data in data.items():
            print(f"Processing repository: {resource_id}")
            resource: GithubResource = GithubResource(
                source_connector='github',
                **resource_data
            )
            resource_collection.resources.append(resource)
            resource_collection.total_count += 1
        return resource_collection

    def _create_info_data_from_resource_collection(
            self,
            resource_collection: GithubResourceCollection
    ) -> GithubInfoData:
        info_data = GithubInfoData(
            repositories=[
                {
                    'name': resource.id,
                    'url': resource.repository_data.basic_info.html_url,
                    'default_branch_name': resource.repository_data.metadata.default_branch,
                }
                for resource in resource_collection.resources
            ]
        )
        return info_data
