"""Tests for verifying YAML schema to JSON data mapping."""
import json
import os
from typing import Any, Dict, List

import pytest
from pydantic import BaseModel

from con_mon_v2.utils.services import ResourceCollectionService


def load_sample_response(provider: str) -> Dict[str, Any]:
    """Load sample response JSON from file."""
    file_path = f"{provider}_response.json"
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Sample response file not found: {file_path}")
    with open(file_path, 'r') as f:
        return json.load(f)


def get_field_value(obj: Any, field_path: str) -> Any:
    """Get value from nested object using dot notation field path."""
    parts = field_path.split('.')
    current = obj
    
    for part in parts[:-1]:  # Process all parts except the last one
        if isinstance(current, list):
            if not current:  # Empty list
                return None
            current = current[0]
        
        if not hasattr(current, part):
            return None
        current = getattr(current, part)
    
    # Handle the last part specially
    last_part = parts[-1]
    if isinstance(current, list):
        if not current:  # Empty list
            return None
        if hasattr(current[0], last_part):
            return getattr(current[0], last_part)
    
    if hasattr(current, last_part):
        return getattr(current, last_part)
    
    return None


def check_field_exists(obj: Any, field_path: str) -> bool:
    """Check if a field exists in the object structure."""
    parts = field_path.split('.')
    current = obj
    
    for part in parts[:-1]:  # Process all parts except the last one
        if isinstance(current, list):
            if not current:  # Empty list
                return False
            current = current[0]
        
        if not hasattr(current, part):
            return False
        current = getattr(current, part)
    
    # Handle the last part specially
    last_part = parts[-1]
    if isinstance(current, list):
        return bool(current) and hasattr(current[0], last_part)
    
    return hasattr(current, last_part)


def test_github_repository_data_mapping():
    """Test GitHub repository_data field mappings."""
    rc_service = ResourceCollectionService('github')
    rc = rc_service.get_resource_collection()
    
    # Basic info fields - all should exist but can be None
    basic_info_paths = [
        'repository_data.basic_info.id',
        'repository_data.basic_info.name',
        'repository_data.basic_info.full_name',
        'repository_data.basic_info.description',  # Can be None
        'repository_data.basic_info.private',
        'repository_data.basic_info.owner',
        'repository_data.basic_info.html_url',
        'repository_data.basic_info.clone_url',
        'repository_data.basic_info.ssh_url',
        'repository_data.basic_info.size',
        'repository_data.basic_info.language',
        'repository_data.basic_info.created_at',
        'repository_data.basic_info.updated_at',
        'repository_data.basic_info.pushed_at',
        'repository_data.basic_info.stargazers_count',
        'repository_data.basic_info.watchers_count',
        'repository_data.basic_info.forks_count',
        'repository_data.basic_info.open_issues_count',
        'repository_data.basic_info.archived',
        'repository_data.basic_info.disabled',
    ]
    
    # Test all basic info paths exist
    for path in basic_info_paths:
        print(f"\nChecking {path}...")
        assert check_field_exists(rc.resources[0], path), f"Field {path} should exist"
        value = get_field_value(rc.resources[0], path)
        print(f"Value: {value}")


def test_github_collaboration_data_mapping():
    """Test GitHub collaboration_data field mappings."""
    rc_service = ResourceCollectionService('github')
    rc = rc_service.get_resource_collection()
    
    # Test pull requests list exists and has items
    pr_list = get_field_value(rc.resources[0], 'collaboration_data.pull_requests')
    assert isinstance(pr_list, list), "pull_requests should be a list"
    assert len(pr_list) > 0, "pull_requests should not be empty"
    
    # Test first pull request has all required fields
    pr_fields = [
        'number', 'title', 'state', 'user', 'created_at', 'updated_at',
        'closed_at', 'merged_at', 'base_branch'
    ]
    for field in pr_fields:
        path = f'collaboration_data.pull_requests.{field}'
        print(f"\nChecking {path}...")
        assert check_field_exists(rc.resources[0], path), f"Field {path} should exist"
        value = get_field_value(rc.resources[0], path)
        print(f"Value: {value}")
    
    # Test collaborators list exists and has items
    collab_list = get_field_value(rc.resources[0], 'collaboration_data.collaborators')
    assert isinstance(collab_list, list), "collaborators should be a list"
    assert len(collab_list) > 0, "collaborators should not be empty"
    
    # Test first collaborator has all required fields
    collab = collab_list[0]
    assert hasattr(collab, 'login'), "collaborator should have login"
    assert hasattr(collab, 'permissions'), "collaborator should have permissions"
    assert hasattr(collab.permissions, 'admin'), "permissions should have admin"
    
    # Test summary fields
    summary_paths = [
        'collaboration_data.total_issues',
        'collaboration_data.open_issues',
        'collaboration_data.closed_issues',
        'collaboration_data.total_pull_requests',
        'collaboration_data.open_pull_requests',
        'collaboration_data.merged_pull_requests',
        'collaboration_data.draft_pull_requests',
    ]
    
    for path in summary_paths:
        print(f"\nChecking {path}...")
        assert check_field_exists(rc.resources[0], path), f"Field {path} should exist"
        value = get_field_value(rc.resources[0], path)
        print(f"Value: {value}")
        assert isinstance(value, int), f"Field {path} should be an integer"


def test_github_security_data_mapping():
    """Test GitHub security_data field mappings."""
    rc_service = ResourceCollectionService('github')
    rc = rc_service.get_resource_collection()
    
    # Test security advisories structure
    advisories = get_field_value(rc.resources[0], 'security_data.security_advisories')
    assert hasattr(advisories, 'error'), "security_advisories should have error field"
    assert hasattr(advisories, 'advisories'), "security_advisories should have advisories list"
    
    # Test vulnerability alerts structure
    alerts = get_field_value(rc.resources[0], 'security_data.vulnerability_alerts')
    assert hasattr(alerts, 'enabled'), "vulnerability_alerts should have enabled field"
    assert hasattr(alerts, 'dependabot_alerts'), "vulnerability_alerts should have dependabot_alerts"
    # error can be None
    
    # Test security analysis fields
    analysis_paths = [
        'security_data.security_analysis.advanced_security_enabled',
        'security_data.security_analysis.secret_scanning_enabled',
        'security_data.security_analysis.push_protection_enabled',
        'security_data.security_analysis.dependency_review_enabled',
    ]
    
    for path in analysis_paths:
        print(f"\nChecking {path}...")
        assert check_field_exists(rc.resources[0], path), f"Field {path} should exist"
        value = get_field_value(rc.resources[0], path)
        print(f"Value: {value}")
        assert isinstance(value, bool), f"Field {path} should be a boolean"


def test_github_advanced_features_data_mapping():
    """Test GitHub advanced_features_data field mappings."""
    rc_service = ResourceCollectionService('github')
    rc = rc_service.get_resource_collection()
    
    # Test tags list exists (can be empty)
    tags = get_field_value(rc.resources[0], 'advanced_features_data.tags')
    assert isinstance(tags, list), "tags should be a list"
    
    # Test webhooks list exists (can be empty)
    webhooks = get_field_value(rc.resources[0], 'advanced_features_data.webhooks')
    assert isinstance(webhooks, list), "webhooks should be a list"
    
    # Test summary fields
    summary_paths = [
        'advanced_features_data.total_tags',
        'advanced_features_data.total_webhooks',
        'advanced_features_data.active_webhooks',
    ]
    
    for path in summary_paths:
        print(f"\nChecking {path}...")
        assert check_field_exists(rc.resources[0], path), f"Field {path} should exist"
        value = get_field_value(rc.resources[0], path)
        print(f"Value: {value}")
        assert isinstance(value, int), f"Field {path} should be an integer"
    
    # Error fields can be None
    error_paths = [
        'advanced_features_data.tags_error',
        'advanced_features_data.webhooks_error',
    ]
    
    for path in error_paths:
        print(f"\nChecking {path}...")
        assert check_field_exists(rc.resources[0], path), f"Field {path} should exist"


def test_github_organization_data_mapping():
    """Test GitHub organization_data field mappings."""
    rc_service = ResourceCollectionService('github')
    rc = rc_service.get_resource_collection()
    
    # Test list fields exist (can be empty)
    list_paths = [
        'organization_data.members',
        'organization_data.teams',
        'organization_data.outside_collaborators',
    ]
    
    for path in list_paths:
        print(f"\nChecking {path}...")
        value = get_field_value(rc.resources[0], path)
        assert isinstance(value, list), f"Field {path} should be a list"
    
    # Test count fields
    count_paths = [
        'organization_data.total_members',
        'organization_data.total_teams',
        'organization_data.total_outside_collaborators',
        'organization_data.admin_members',
    ]
    
    for path in count_paths:
        print(f"\nChecking {path}...")
        value = get_field_value(rc.resources[0], path)
        assert isinstance(value, int), f"Field {path} should be an integer"
    
    # Test error fields exist (can be None)
    error_paths = [
        'organization_data.members_error',
        'organization_data.teams_error',
        'organization_data.collaborators_error',
    ]
    
    for path in error_paths:
        print(f"\nChecking {path}...")
        assert check_field_exists(rc.resources[0], path), f"Field {path} should exist" 