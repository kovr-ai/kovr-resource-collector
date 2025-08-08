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
        print(f"Value: {value}")
    
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
        print(f"Value: {value}")
    
    # Test error fields exist (can be None)
    error_paths = [
        'organization_data.members_error',
        'organization_data.teams_error',
        'organization_data.collaborators_error',
    ]
    
    for path in error_paths:
        print(f"\nChecking {path}...")
        assert check_field_exists(rc.resources[0], path), f"Field {path} should exist"
        value = get_field_value(rc.resources[0], path)
        print(f"Value: {value}")


def test_aws_ec2_resource_mapping():
    """Test AWS EC2 resource field mappings."""
    rc_service = ResourceCollectionService('aws')
    rc = rc_service.get_resource_collection()
    
    # Find EC2 resource in the collection
    ec2_resource = next((r for r in rc.resources if r.__class__.__name__ == 'EC2Resource'), None)
    assert ec2_resource is not None, "EC2Resource not found in collection"
    
    # Test instance fields
    instance_paths = [
        'instances',  # Dictionary of instance_id -> instance_data
    ]
    
    for path in instance_paths:
        print(f"\nChecking EC2 {path}...")
        assert check_field_exists(ec2_resource, path), f"Field {path} should exist"
        value = get_field_value(ec2_resource, path)
        print(f"Value: {value}")
        
        # Test instance fields if instances exist
        if value:
            instance = list(value.values())[0]  # Get first instance
            instance_fields = [
                'instance_id', 'instance_type', 'state', 'private_ip_address',
                'public_ip_address', 'launch_time', 'vpc_id', 'subnet_id',
                'availability_zone', 'security_groups'
            ]
            for field in instance_fields:
                print(f"\nChecking instance.{field}...")
                assert hasattr(instance, field), f"Instance should have {field}"
                print(f"Value: {getattr(instance, field)}")

    # Test VPC fields
    vpc_paths = [
        'vpcs',  # Dictionary of vpc_id -> vpc_data
    ]
    
    for path in vpc_paths:
        print(f"\nChecking EC2 {path}...")
        assert check_field_exists(ec2_resource, path), f"Field {path} should exist"
        value = get_field_value(ec2_resource, path)
        print(f"Value: {value}")
        
        # Test VPC fields if VPCs exist
        if value:
            vpc = list(value.values())[0]  # Get first VPC
            vpc_fields = [
                'vpc_id', 'state', 'cidr_block', 'dhcp_options_id',
                'instance_tenancy', 'is_default'
            ]
            for field in vpc_fields:
                print(f"\nChecking vpc.{field}...")
                assert hasattr(vpc, field), f"VPC should have {field}"
                print(f"Value: {getattr(vpc, field)}")


def test_aws_iam_resource_mapping():
    """Test AWS IAM resource field mappings."""
    rc_service = ResourceCollectionService('aws')
    rc = rc_service.get_resource_collection()
    
    # Find IAM resource in the collection
    iam_resource = next((r for r in rc.resources if r.__class__.__name__ == 'IAMResource'), None)
    assert iam_resource is not None, "IAMResource not found in collection"
    
    # Test users dictionary
    print("\nChecking IAM users...")
    assert hasattr(iam_resource, 'users'), "IAM resource should have users"
    users = iam_resource.users
    print(f"Users: {users}")
    
    if users:
        user = list(users.values())[0]  # Get first user
        user_fields = [
            'arn', 'user_id', 'create_date', 'path',
            'access_keys', 'mfa_devices'
        ]
        for field in user_fields:
            print(f"\nChecking user.{field}...")
            assert hasattr(user, field), f"User should have {field}"
            print(f"Value: {getattr(user, field)}")
    
    # Test policies dictionary
    print("\nChecking IAM policies...")
    assert hasattr(iam_resource, 'policies'), "IAM resource should have policies"
    policies = iam_resource.policies
    print(f"Policies: {policies}")
    
    if policies:
        policy = list(policies.values())[0]  # Get first policy
        policy_fields = [
            'policy_name', 'policy_id', 'create_date', 'update_date',
            'path', 'default_version_id', 'attachment_count'
        ]
        for field in policy_fields:
            print(f"\nChecking policy.{field}...")
            assert hasattr(policy, field), f"Policy should have {field}"
            print(f"Value: {getattr(policy, field)}")


def test_aws_s3_resource_mapping():
    """Test AWS S3 resource field mappings."""
    rc_service = ResourceCollectionService('aws')
    rc = rc_service.get_resource_collection()
    
    # Find S3 resource in the collection
    s3_resource = next((r for r in rc.resources if r.__class__.__name__ == 'S3Resource'), None)
    assert s3_resource is not None, "S3Resource not found in collection"
    
    # Test buckets dictionary
    print("\nChecking S3 buckets...")
    assert hasattr(s3_resource, 'buckets'), "S3 resource should have buckets"
    buckets = s3_resource.buckets
    print(f"Buckets: {buckets}")
    
    if buckets:
        bucket = list(buckets.values())[0]  # Get first bucket
        bucket_fields = [
            'name', 'creation_date', 'region',
            'versioning_enabled', 'logging_enabled',
            'public_access_blocked', 'encryption_enabled'
        ]
        for field in bucket_fields:
            print(f"\nChecking bucket.{field}...")
            assert hasattr(bucket, field), f"Bucket should have {field}"
            print(f"Value: {getattr(bucket, field)}")


def test_aws_cloudwatch_resource_mapping():
    """Test AWS CloudWatch resource field mappings."""
    rc_service = ResourceCollectionService('aws')
    rc = rc_service.get_resource_collection()
    
    # Find CloudWatch resource in the collection
    cw_resource = next((r for r in rc.resources if r.__class__.__name__ == 'CloudWatchResource'), None)
    assert cw_resource is not None, "CloudWatchResource not found in collection"
    
    # Test log groups dictionary
    print("\nChecking CloudWatch log groups...")
    assert hasattr(cw_resource, 'log_groups'), "CloudWatch resource should have log_groups"
    log_groups = cw_resource.log_groups
    print(f"Log Groups: {log_groups}")
    
    if log_groups:
        log_group = list(log_groups.values())[0]  # Get first log group
        log_group_fields = [
            'log_group_name', 'creation_time', 'retention_in_days',
            'metric_filter_count', 'arn', 'stored_bytes'
        ]
        for field in log_group_fields:
            print(f"\nChecking log_group.{field}...")
            assert hasattr(log_group, field), f"Log group should have {field}"
            print(f"Value: {getattr(log_group, field)}")
    
    # Test metrics list
    print("\nChecking CloudWatch metrics...")
    assert hasattr(cw_resource, 'metrics'), "CloudWatch resource should have metrics"
    metrics = cw_resource.metrics
    print(f"Metrics: {metrics}")
    
    if metrics:
        metric = metrics[0]  # Get first metric
        metric_fields = ['namespace', 'metric_name', 'dimensions']
        for field in metric_fields:
            print(f"\nChecking metric.{field}...")
            assert hasattr(metric, field), f"Metric should have {field}"
            print(f"Value: {getattr(metric, field)}")


def test_aws_cloudtrail_resource_mapping():
    """Test AWS CloudTrail resource field mappings."""
    rc_service = ResourceCollectionService('aws')
    rc = rc_service.get_resource_collection()
    
    # Find CloudTrail resource in the collection
    ct_resource = next((r for r in rc.resources if r.__class__.__name__ == 'CloudTrailResource'), None)
    assert ct_resource is not None, "CloudTrailResource not found in collection"
    
    # Test trails dictionary
    print("\nChecking CloudTrail trails...")
    assert hasattr(ct_resource, 'trails'), "CloudTrail resource should have trails"
    trails = ct_resource.trails
    print(f"Trails: {trails}")
    
    if trails:
        trail = list(trails.values())[0]  # Get first trail
        trail_fields = [
            'name', 'arn', 'is_multi_region_trail',
            'home_region', 'log_file_validation_enabled',
            'cloud_watch_logs_log_group_arn',
            'cloud_watch_logs_role_arn',
            'kms_key_id'
        ]
        for field in trail_fields:
            print(f"\nChecking trail.{field}...")
            assert hasattr(trail, field), f"Trail should have {field}"
            print(f"Value: {getattr(trail, field)}")
    
    # Test event selectors
    print("\nChecking CloudTrail event selectors...")
    assert hasattr(ct_resource, 'event_selectors'), "CloudTrail resource should have event_selectors"
    event_selectors = ct_resource.event_selectors
    print(f"Event Selectors: {event_selectors}")
    
    if event_selectors:
        selector = event_selectors[0]  # Get first selector
        selector_fields = [
            'read_write_type', 'include_management_events',
            'data_resources'
        ]
        for field in selector_fields:
            print(f"\nChecking event_selector.{field}...")
            assert hasattr(selector, field), f"Event selector should have {field}"
            print(f"Value: {getattr(selector, field)}")


if __name__ == "__main__":
    test_aws_ec2_resource_mapping()
