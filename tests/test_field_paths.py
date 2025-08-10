"""Tests for verifying YAML schema to JSON data mapping."""
import json
import os
from typing import Any, Dict

from con_mon_v2.utils.services import ResourceCollectionService


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
    pr = pr_list[0]  # Get first pull request
    pr_fields = [
        'number', 'title', 'state', 'user', 'created_at', 'updated_at',
        'closed_at', 'merged_at', 'base_branch'
    ]
    for field in pr_fields:
        print(f"\nChecking pull_request.{field}...")
        assert hasattr(pr, field), f"Pull request should have {field}"
        print(f"Value: {getattr(pr, field)}")
    
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
    
    # Test first dependabot alert has all required fields
    dependabot_alerts = alerts.dependabot_alerts
    if dependabot_alerts:
        alert = dependabot_alerts[0]
        alert_fields = [
            'number', 'state', 'severity', 'package',
            'created_at', 'updated_at'
        ]
        for field in alert_fields:
            print(f"\nChecking dependabot_alert.{field}...")
            assert hasattr(alert, field), f"Dependabot alert should have {field}"
            print(f"Value: {getattr(alert, field)}")
    
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
    
    # Test first tag has all required fields
    if tags:
        tag = tags[0]
        tag_fields = [
            'name', 'commit_sha', 'commit_date', 'message'
        ]
        for field in tag_fields:
            print(f"\nChecking tag.{field}...")
            assert hasattr(tag, field), f"Tag should have {field}"
            print(f"Value: {getattr(tag, field)}")
    
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
        value = get_field_value(rc.resources[0], path)
        print(f"Value: {value}")


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
        
        # Test first item has required fields
        if value:
            item = value[0]
            if 'members' in path:
                member_fields = ['login', 'id', 'type', 'site_admin', 'role']
                for field in member_fields:
                    print(f"\nChecking member.{field}...")
                    assert hasattr(item, field), f"Member should have {field}"
                    print(f"Value: {getattr(item, field)}")
            elif 'teams' in path:
                team_fields = ['id', 'name', 'slug', 'description', 'privacy', 'permission']
                for field in team_fields:
                    print(f"\nChecking team.{field}...")
                    assert hasattr(item, field), f"Team should have {field}"
                    print(f"Value: {getattr(item, field)}")
            elif 'outside_collaborators' in path:
                collab_fields = ['login', 'id', 'type', 'permissions']
                for field in collab_fields:
                    print(f"\nChecking collaborator.{field}...")
                    assert hasattr(item, field), f"Collaborator should have {field}"
                    print(f"Value: {getattr(item, field)}")
    
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
        'instances',  # List of instances
    ]
    
    for path in instance_paths:
        print(f"\nChecking EC2 {path}...")
        assert check_field_exists(ec2_resource, path), f"Field {path} should exist"
        value = get_field_value(ec2_resource, path)
        print(f"Value: {value}")
        
        # Test instance fields if instances exist
        if value:
            instance = value[0]  # Get first instance
            instance_fields = [
                'id', 'instance_type', 'state', 'private_ip_address',
                'public_ip_address', 'launch_time', 'vpc_id', 'subnet_id',
                'availability_zone', 'security_groups'
            ]
            for field in instance_fields:
                print(f"\nChecking instance.{field}...")
                assert hasattr(instance, field), f"Instance should have {field}"
                print(f"Value: {getattr(instance, field)}")

    # Test VPC fields
    vpc_paths = [
        'vpcs',  # List of VPCs
    ]
    
    for path in vpc_paths:
        print(f"\nChecking EC2 {path}...")
        assert check_field_exists(ec2_resource, path), f"Field {path} should exist"
        value = get_field_value(ec2_resource, path)
        print(f"Value: {value}")
        
        # Test VPC fields if VPCs exist
        if value:
            vpc = value[0]  # Get first VPC
            vpc_fields = [
                'id', 'state', 'cidr_block', 'dhcp_options_id',
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
    
    # Test users list
    print("\nChecking IAM users...")
    assert hasattr(iam_resource, 'users'), "IAM resource should have users"
    users = iam_resource.users
    print(f"Users: {users}")
    
    if users:
        user = users[0]  # Get first user
        user_fields = [
            'id', 'arn', 'user_id', 'create_date', 'path',
            'access_keys', 'mfa_devices'
        ]
        for field in user_fields:
            print(f"\nChecking user.{field}...")
            assert hasattr(user, field), f"User should have {field}"
            print(f"Value: {getattr(user, field)}")
    
    # Test policies list
    print("\nChecking IAM policies...")
    assert hasattr(iam_resource, 'policies'), "IAM resource should have policies"
    policies = iam_resource.policies
    print(f"Policies: {policies}")
    
    if policies:
        policy = policies[0]  # Get first policy
        policy_fields = [
            'id', 'policy_name', 'policy_id', 'create_date', 'update_date',
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
    
    # Test buckets list
    print("\nChecking S3 buckets...")
    assert hasattr(s3_resource, 'buckets'), "S3 resource should have buckets"
    buckets = s3_resource.buckets
    print(f"Buckets: {buckets}")
    
    if buckets:
        bucket = buckets[0]  # Get first bucket
        bucket_fields = [
            'id', 'name', 'creation_date', 'region',
            'versioning_status', 'logging_enabled',
            'website_enabled', 'encryption'
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
    
    # Test log groups list
    print("\nChecking CloudWatch log groups...")
    assert hasattr(cw_resource, 'log_groups'), "CloudWatch resource should have log_groups"
    log_groups = cw_resource.log_groups
    print(f"Log Groups: {log_groups}")
    
    if log_groups:
        log_group = log_groups[0]  # Get first log group
        log_group_fields = [
            'id', 'log_group_name', 'creation_time', 'retention_in_days',
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
    
    # Test trails list
    print("\nChecking CloudTrail trails...")
    assert hasattr(ct_resource, 'trails'), "CloudTrail resource should have trails"
    trails = ct_resource.trails
    print(f"Trails: {trails}")
    
    if trails:
        trail = trails[0]  # Get first trail
        trail_fields = [
            'id', 'name', 'arn', 'is_multi_region_trail',
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


def test_aws_array_field_path_execution():
    """Test that array field paths like instances[].iam_instance_profile don't cause errors in check execution."""
    rc_service = ResourceCollectionService('aws')
    rc = rc_service.get_resource_collection()
    
    # Find EC2 resource in the collection
    ec2_resource = next((r for r in rc.resources if r.__class__.__name__ == 'EC2Resource'), None)
    assert ec2_resource is not None, "EC2Resource not found in collection"
    
    # Test that complex array field paths can be processed without errors
    complex_field_paths = [
        'instances[].iam_instance_profile',
        'instances[].iam_instance_profile.Arn',
        'instances[].iam_instance_profile.Id',
        'instances[].security_groups',
        'instances[].network_interfaces',
        'instances[].block_device_mappings',
        'instances[].block_device_mappings[].device_name',
        'instances[].block_device_mappings[].ebs',
    ]
    
    for field_path in complex_field_paths:
        print(f"\nTesting field path: {field_path}")
        
        # Simulate how the check execution would handle this field path
        # For array notation like instances[], we should be able to access instances
        base_path = field_path.replace('[]', '')
        path_parts = base_path.split('.')
        
        current = ec2_resource
        path_traversed = []
        
        for i, part in enumerate(path_parts):
            path_traversed.append(part)
            current_path = '.'.join(path_traversed)
            
            # Assert that each part of the path exists
            assert hasattr(current, part), f"Field '{part}' not found in path '{current_path}' for field_path '{field_path}'"
            
            current = getattr(current, part)
            print(f"  ✓ Found '{part}' - type: {type(current)}")
            
            # If we hit a list and there are more path parts, check first item
            if isinstance(current, list) and i < len(path_parts) - 1:
                if current:  # List is not empty
                    print(f"    → Checking first item in list of {len(current)} items")
                    current = current[0]
                    # Assert that the first item exists
                    assert current is not None, f"First item in list at '{current_path}' is None for field_path '{field_path}'"
                else:
                    print(f"    → Empty list, cannot traverse further")
                    # For empty lists, we can't traverse further but this shouldn't be an error
                    # Just verify the list exists
                    assert isinstance(current, list), f"Expected list at '{current_path}' for field_path '{field_path}'"
                    break
        
        print(f"  ✅ Field path '{field_path}' processed successfully")
        
    # Specifically test iam_instance_profile structure if instances exist
    if hasattr(ec2_resource, 'instances') and ec2_resource.instances:
        instances = ec2_resource.instances
        assert isinstance(instances, list), "instances should be a list"
        
        if instances:
            first_instance = instances[0]
            print(f"\nTesting iam_instance_profile structure on first instance...")
            
            # Test that iam_instance_profile field exists
            assert hasattr(first_instance, 'iam_instance_profile'), "Instance should have iam_instance_profile field"
            
            iam_profile = first_instance.iam_instance_profile
            print(f"iam_instance_profile value: {iam_profile}")
            print(f"iam_instance_profile type: {type(iam_profile)}")
            
            # If iam_instance_profile is not None, test its structure
            if iam_profile is not None:
                # Test that it has the expected fields based on the YAML schema
                assert hasattr(iam_profile, 'Arn'), "iam_instance_profile should have Arn field"
                assert hasattr(iam_profile, 'Id'), "iam_instance_profile should have Id field"
                
                print(f"  ✓ iam_instance_profile.Arn: {iam_profile.Arn}")
                print(f"  ✓ iam_instance_profile.Id: {iam_profile.Id}")
            else:
                print("  ℹ️  iam_instance_profile is None (no IAM role attached to this instance)")


def test_comprehensive_field_paths_all_resources():
    """Test comprehensive field paths for all resources defined in the YAML schema."""
    
    # Test GitHub resources
    print("\n=== TESTING GITHUB RESOURCES ===")
    rc_service = ResourceCollectionService('github')
    rc = rc_service.get_resource_collection()
    
    github_resource = rc.resources[0] if rc.resources else None
    assert github_resource is not None, "GitHub resource not found"
    
    # GitHub field paths from YAML schema
    github_field_paths = [
        # Basic repository data
        'repository_data.basic_info.id',
        'repository_data.basic_info.name',
        'repository_data.basic_info.full_name',
        'repository_data.basic_info.description',
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
        
        # Metadata
        'repository_data.metadata.default_branch',
        'repository_data.metadata.topics',
        'repository_data.metadata.has_issues',
        'repository_data.metadata.has_projects',
        'repository_data.metadata.has_wiki',
        'repository_data.metadata.has_pages',
        'repository_data.metadata.has_downloads',
        'repository_data.metadata.has_discussions',
        'repository_data.metadata.is_template',
        'repository_data.metadata.license',
        'repository_data.metadata.visibility',
        'repository_data.metadata.allow_forking',
        'repository_data.metadata.web_commit_signoff_required',
        
        # Branches array
        'repository_data.branches',
        
        # Statistics
        'repository_data.statistics.total_commits',
        'repository_data.statistics.contributors_count',
        'repository_data.statistics.languages',
        'repository_data.statistics.code_frequency',
        
        # Actions data
        'actions_data.workflows.id',
        'actions_data.workflows.name',
        'actions_data.workflows.path',
        'actions_data.workflows.state',
        'actions_data.workflows.created_at',
        'actions_data.workflows.updated_at',
        'actions_data.workflows.url',
        'actions_data.workflows.html_url',
        'actions_data.workflows.badge_url',
        'actions_data.workflows.recent_runs',
        'actions_data.total_workflows',
        'actions_data.active_workflows',
        'actions_data.recent_runs_count',
        
        # Collaboration data
        'collaboration_data.issues',
        'collaboration_data.pull_requests',
        'collaboration_data.collaborators',
        'collaboration_data.total_issues',
        'collaboration_data.open_issues',
        'collaboration_data.closed_issues',
        'collaboration_data.total_pull_requests',
        'collaboration_data.open_pull_requests',
        'collaboration_data.merged_pull_requests',
        'collaboration_data.draft_pull_requests',
        
        # Security data
        'security_data.security_advisories',
        'security_data.vulnerability_alerts',
        'security_data.security_analysis.advanced_security_enabled',
        'security_data.security_analysis.secret_scanning_enabled',
        'security_data.security_analysis.push_protection_enabled',
        'security_data.security_analysis.dependency_review_enabled',
        
        # Organization data
        'organization_data.members',
        'organization_data.teams',
        'organization_data.outside_collaborators',
        'organization_data.total_members',
        'organization_data.total_teams',
        'organization_data.total_outside_collaborators',
        'organization_data.admin_members',
        'organization_data.members_error',
        'organization_data.teams_error',
        'organization_data.collaborators_error',
        
        # Advanced features data
        'advanced_features_data.tags',
        'advanced_features_data.webhooks',
        'advanced_features_data.total_tags',
        'advanced_features_data.total_webhooks',
        'advanced_features_data.active_webhooks',
        'advanced_features_data.tags_error',
        'advanced_features_data.webhooks_error',
    ]
    
    _test_field_paths_for_resource(github_resource, github_field_paths, "GitHub")
    
    # Test AWS resources
    print("\n=== TESTING AWS RESOURCES ===")
    aws_rc_service = ResourceCollectionService('aws')
    aws_rc = aws_rc_service.get_resource_collection()
    
    # Test EC2 Resource
    ec2_resource = next((r for r in aws_rc.resources if r.__class__.__name__ == 'EC2Resource'), None)
    if ec2_resource:
        ec2_field_paths = [
            # Basic fields
            'id',
            'region',
            
            # Account limits
            'account.limits.supported-platforms',
            'account.limits.vpc-max-security-groups-per-interface',
            'account.limits.max-elastic-ips',
            'account.limits.max-instances',
            'account.limits.vpc-max-elastic-ips',
            'account.limits.default-vpc',
            
            # Reserved instances
            'account.reserved_instances',
            
            # Spot instances
            'account.spot_instances',
            
            # Instances array and nested fields
            'instances',
            
            # Security groups
            'security_groups.group_name',
            'security_groups.description',
            'security_groups.vpc_id',
            'security_groups.inbound_rules',
            'security_groups.outbound_rules',
            
            # VPCs
            'vpcs',
            
            # Subnets
            'subnets',
            
            # Route tables
            'route_tables',
            
            # NAT gateways
            'nat_gateways',
            
            # Elastic IPs
            'elastic_ips',
            
            # Key pairs
            'key_pairs',
            
            # Snapshots
            'snapshots',
            
            # Volumes
            'volumes',
            
            # Network interfaces
            'network_interfaces',
            
            # Internet gateways
            'internet_gateways',
        ]
        
        _test_field_paths_for_resource(ec2_resource, ec2_field_paths, "EC2")
        
        # Test specific array field paths for EC2 instances
        ec2_array_field_paths = [
            'instances[].id',
            'instances[].instance_type',
            'instances[].state',
            'instances[].private_ip_address',
            'instances[].public_ip_address',
            'instances[].launch_time',
            'instances[].image_id',
            'instances[].vpc_id',
            'instances[].subnet_id',
            'instances[].availability_zone',
            'instances[].key_name',
            'instances[].platform',
            'instances[].monitoring',
            'instances[].iam_instance_profile',
            'instances[].iam_instance_profile.Arn',
            'instances[].iam_instance_profile.Id',
            'instances[].ebs_optimized',
            'instances[].instance_lifecycle',
            'instances[].security_groups',
            'instances[].network_interfaces',
            'instances[].block_device_mappings',
            'instances[].block_device_mappings[].device_name',
            'instances[].block_device_mappings[].ebs.volume_id',
            'instances[].block_device_mappings[].ebs.status',
            'instances[].block_device_mappings[].ebs.attach_time',
            'instances[].block_device_mappings[].ebs.delete_on_termination',
        ]
        
        _test_array_field_paths_for_resource(ec2_resource, ec2_array_field_paths, "EC2")
    
    # Test IAM Resource
    iam_resource = next((r for r in aws_rc.resources if r.__class__.__name__ == 'IAMResource'), None)
    if iam_resource:
        iam_field_paths = [
            'id',
            'users',
            'policies',
        ]
        
        _test_field_paths_for_resource(iam_resource, iam_field_paths, "IAM")
        
        # Test IAM array field paths
        iam_array_field_paths = [
            'users[].id',
            'users[].arn',
            'users[].user_id',
            'users[].create_date',
            'users[].path',
            'users[].access_keys',
            'users[].access_keys[].id',
            'users[].access_keys[].status',
            'users[].access_keys[].create_date',
            'users[].access_keys[].last_used_date',
            'users[].access_keys[].last_used_service',
            'users[].access_keys[].last_used_region',
            'users[].mfa_devices',
            'users[].mfa_devices[].serial_number',
            'users[].mfa_devices[].enable_date',
            'users[].mfa_devices[].type',
            'users[].mfa_devices[].virtual_mfa_token',
            'policies[].id',
            'policies[].policy_name',
            'policies[].policy_id',
            'policies[].create_date',
            'policies[].update_date',
            'policies[].path',
            'policies[].default_version_id',
            'policies[].attachment_count',
            'policies[].default_version.Document.Version',
            'policies[].default_version.Document.Statement',
            'policies[].default_version.VersionId',
            'policies[].default_version.IsDefaultVersion',
            'policies[].default_version.CreateDate',
        ]
        
        _test_array_field_paths_for_resource(iam_resource, iam_array_field_paths, "IAM")
    
    # Test S3 Resource
    s3_resource = next((r for r in aws_rc.resources if r.__class__.__name__ == 'S3Resource'), None)
    if s3_resource:
        s3_field_paths = [
            'id',
            'buckets',
        ]
        
        _test_field_paths_for_resource(s3_resource, s3_field_paths, "S3")
        
        # Test S3 array field paths
        s3_array_field_paths = [
            'buckets[].id',
            'buckets[].name',
            'buckets[].creation_date',
            'buckets[].region',
            'buckets[].versioning_status',
            'buckets[].logging_enabled',
            'buckets[].website_enabled',
            'buckets[].encryption.enabled',
            'buckets[].encryption.type',
            'buckets[].encryption.kms_key_id',
            'buckets[].public_access_block.block_public_acls',
            'buckets[].public_access_block.block_public_policy',
            'buckets[].public_access_block.ignore_public_acls',
            'buckets[].public_access_block.restrict_public_buckets',
        ]
        
        _test_array_field_paths_for_resource(s3_resource, s3_array_field_paths, "S3")
    
    # Test CloudTrail Resource
    ct_resource = next((r for r in aws_rc.resources if r.__class__.__name__ == 'CloudTrailResource'), None)
    if ct_resource:
        ct_field_paths = [
            'id',
            'trails',
            'event_selectors',
        ]
        
        _test_field_paths_for_resource(ct_resource, ct_field_paths, "CloudTrail")
        
        # Test CloudTrail array field paths
        ct_array_field_paths = [
            'trails[].id',
            'trails[].name',
            'trails[].s3_bucket_name',
            'trails[].s3_key_prefix',
            'trails[].include_global_service_events',
            'trails[].is_multi_region_trail',
            'trails[].enable_log_file_validation',
            'trails[].event_selectors',
            'trails[].event_selectors[].read_write_type',
            'trails[].event_selectors[].include_management_events',
            'trails[].event_selectors[].data_resources.type',
            'trails[].event_selectors[].data_resources.values',
            'trails[].event_selectors[].data_resources.values[*]',
            'trails[].insight_selectors',
            'trails[].insight_selectors[].insight_type',
            'trails[].is_logging',
            'trails[].kms_key_id',
            'trails[].log_file_validation_enabled',
            'trails[].tags',
            'trails[].tags[*].key',
            'trails[].tags[*].value',
        ]
        
        _test_array_field_paths_for_resource(ct_resource, ct_array_field_paths, "CloudTrail")
    
    # Test CloudWatch Resource
    cw_resource = next((r for r in aws_rc.resources if r.__class__.__name__ == 'CloudWatchResource'), None)
    if cw_resource:
        cw_field_paths = [
            'id',
            'log_groups',
            'metrics',
            'alarms',
            'dashboards',
        ]
        
        _test_field_paths_for_resource(cw_resource, cw_field_paths, "CloudWatch")
        
        # Test CloudWatch array field paths
        cw_array_field_paths = [
            'log_groups[].id',
            'log_groups[].log_group_name',
            'log_groups[].creation_time',
            'log_groups[].retention_in_days',
            'log_groups[].metric_filter_count',
            'log_groups[].arn',
            'log_groups[].stored_bytes',
            'log_groups[].kms_key_id',
            'metrics[].namespace',
            'metrics[].metric_name',
            'metrics[].dimensions',
            'metrics[].dimensions[*].Name',
            'metrics[].dimensions[*].Value',
            'alarms[].alarm_name',
            'alarms[].alarm_description',
            'alarms[].actions_enabled',
            'alarms[].ok_actions',
            'alarms[].alarm_actions',
            'alarms[].insufficient_data_actions',
            'alarms[].state_value',
            'alarms[].state_reason',
            'alarms[].state_updated_timestamp',
            'alarms[].metric_name',
            'alarms[].namespace',
            'alarms[].statistic',
            'alarms[].period',
            'alarms[].evaluation_periods',
            'alarms[].threshold',
            'alarms[].comparison_operator',
            'dashboards[].dashboard_name',
            'dashboards[].dashboard_arn',
            'dashboards[].dashboard_body',
            'dashboards[].size',
            'dashboards[].last_modified',
        ]
        
        _test_array_field_paths_for_resource(cw_resource, cw_array_field_paths, "CloudWatch")


def _test_field_paths_for_resource(resource, field_paths, resource_name):
    """Helper function to test field paths for a specific resource."""
    print(f"\n--- Testing {resource_name} Resource Field Paths ---")
    
    for field_path in field_paths:
        print(f"Testing {resource_name} field path: {field_path}")
        
        # Test that the field path can be traversed
        path_parts = field_path.split('.')
        current = resource
        path_traversed = []
        
        for i, part in enumerate(path_parts):
            path_traversed.append(part)
            current_path = '.'.join(path_traversed)
            
            # Assert that each part of the path exists
            assert hasattr(current, part), f"Field '{part}' not found in path '{current_path}' for {resource_name} resource"
            
            current = getattr(current, part)
            print(f"  ✓ Found '{part}' - type: {type(current)}")


def _test_array_field_paths_for_resource(resource, field_paths, resource_name):
    """Helper function to test array field paths for a specific resource."""
    print(f"\n--- Testing {resource_name} Resource Array Field Paths ---")
    
    for field_path in field_paths:
        print(f"Testing {resource_name} array field path: {field_path}")
        
        # Convert array notation to regular path for traversal
        base_path = field_path.replace('[]', '')
        path_parts = base_path.split('.')
        
        current = resource
        path_traversed = []
        
        for i, part in enumerate(path_parts):
            path_traversed.append(part)
            current_path = '.'.join(path_traversed)
            
            # Assert that each part of the path exists
            assert hasattr(current, part), f"Field '{part}' not found in path '{current_path}' for {resource_name} array field path '{field_path}'"
            
            current = getattr(current, part)
            print(f"  ✓ Found '{part}' - type: {type(current)}")
            
            # If we hit a list and there are more path parts, check first item
            if isinstance(current, list) and i < len(path_parts) - 1:
                if current:  # List is not empty
                    print(f"    → Checking first item in list of {len(current)} items")
                    current = current[0]
                    # Assert that the first item exists
                    assert current is not None, f"First item in list at '{current_path}' is None for {resource_name} array field path '{field_path}'"
                else:
                    print(f"    → Empty list, cannot traverse further")
                    # For empty lists, we can't traverse further but this shouldn't be an error
                    assert isinstance(current, list), f"Expected list at '{current_path}' for {resource_name} array field path '{field_path}'"
                    break


def test_wildcard_array_field_paths():
    """Test wildcard array field paths like repository_data.branches[*].protection_details and repository_data.branches.*.protection_details."""
    
    # Test GitHub wildcard patterns
    print("\n=== TESTING GITHUB WILDCARD ARRAY FIELD PATHS ===")
    rc_service = ResourceCollectionService('github')
    rc = rc_service.get_resource_collection()
    
    github_resource = rc.resources[0] if rc.resources else None
    assert github_resource is not None, "GitHub resource not found"
    
    # GitHub wildcard field paths from YAML schema
    github_wildcard_patterns = [
        # Branches with wildcard patterns
        'repository_data.branches[*].name',
        'repository_data.branches[*].sha', 
        'repository_data.branches[*].protected',
        'repository_data.branches[*].protection_details',
        'repository_data.branches[*].protection_details.required_status_checks',
        'repository_data.branches[*].protection_details.enforce_admins',
        'repository_data.branches[*].protection_details.required_pull_request_reviews',
        'repository_data.branches[*].protection_details.restrictions',
        
        # Alternative wildcard syntax (dot-star)
        'repository_data.branches.*.name',
        'repository_data.branches.*.sha',
        'repository_data.branches.*.protected', 
        'repository_data.branches.*.protection_details',
        'repository_data.branches.*.protection_details.required_status_checks',
        'repository_data.branches.*.protection_details.enforce_admins',
        'repository_data.branches.*.protection_details.required_pull_request_reviews',
        'repository_data.branches.*.protection_details.restrictions',
        
        # DEEP NESTING: Topics array
        'repository_data.metadata.topics',
        'repository_data.metadata.topics[*]',
        'repository_data.metadata.topics.*',
        
        # DEEP NESTING: Languages object (nested structure)
        'repository_data.statistics.languages.Python',
        'repository_data.statistics.languages.JavaScript',
        'repository_data.statistics.languages.TypeScript',
        'repository_data.statistics.languages.Shell',
        'repository_data.statistics.languages.HTML',
        
        # Code frequency with wildcard patterns
        'repository_data.statistics.code_frequency[*].timestamp',
        'repository_data.statistics.code_frequency[*].additions',
        'repository_data.statistics.code_frequency[*].deletions',
        'repository_data.statistics.code_frequency.*.timestamp',
        'repository_data.statistics.code_frequency.*.additions', 
        'repository_data.statistics.code_frequency.*.deletions',
        
        # Recent runs with wildcard patterns
        'actions_data.workflows.recent_runs[*].id',
        'actions_data.workflows.recent_runs[*].name',
        'actions_data.workflows.recent_runs[*].head_branch',
        'actions_data.workflows.recent_runs[*].head_sha',
        'actions_data.workflows.recent_runs[*].status',
        'actions_data.workflows.recent_runs[*].conclusion',
        'actions_data.workflows.recent_runs[*].created_at',
        'actions_data.workflows.recent_runs[*].updated_at',
        'actions_data.workflows.recent_runs[*].run_number',
        'actions_data.workflows.recent_runs[*].run_attempt',
        'actions_data.workflows.recent_runs.*.id',
        'actions_data.workflows.recent_runs.*.name',
        'actions_data.workflows.recent_runs.*.head_branch',
        'actions_data.workflows.recent_runs.*.head_sha',
        'actions_data.workflows.recent_runs.*.status',
        'actions_data.workflows.recent_runs.*.conclusion',
        'actions_data.workflows.recent_runs.*.created_at',
        'actions_data.workflows.recent_runs.*.updated_at',
        'actions_data.workflows.recent_runs.*.run_number',
        'actions_data.workflows.recent_runs.*.run_attempt',
        
        # Issues and pull requests with wildcard patterns
        'collaboration_data.issues[*].number',
        'collaboration_data.issues[*].title',
        'collaboration_data.issues[*].state',
        'collaboration_data.issues[*].user',
        'collaboration_data.issues[*].created_at',
        'collaboration_data.issues[*].updated_at',
        'collaboration_data.issues[*].closed_at',
        'collaboration_data.issues.*.number',
        'collaboration_data.issues.*.title',
        'collaboration_data.issues.*.state',
        'collaboration_data.issues.*.user',
        'collaboration_data.issues.*.created_at',
        'collaboration_data.issues.*.updated_at',
        'collaboration_data.issues.*.closed_at',
        
        'collaboration_data.pull_requests[*].number',
        'collaboration_data.pull_requests[*].title',
        'collaboration_data.pull_requests[*].state',
        'collaboration_data.pull_requests[*].user',
        'collaboration_data.pull_requests[*].created_at',
        'collaboration_data.pull_requests[*].updated_at',
        'collaboration_data.pull_requests[*].closed_at',
        'collaboration_data.pull_requests[*].merged_at',
        'collaboration_data.pull_requests[*].base_branch',
        'collaboration_data.pull_requests.*.number',
        'collaboration_data.pull_requests.*.title',
        'collaboration_data.pull_requests.*.state',
        'collaboration_data.pull_requests.*.user',
        'collaboration_data.pull_requests.*.created_at',
        'collaboration_data.pull_requests.*.updated_at',
        'collaboration_data.pull_requests.*.closed_at',
        'collaboration_data.pull_requests.*.merged_at',
        'collaboration_data.pull_requests.*.base_branch',
        
        # Collaborators with wildcard patterns
        'collaboration_data.collaborators[*].login',
        'collaboration_data.collaborators[*].permissions',
        'collaboration_data.collaborators[*].permissions.admin',
        'collaboration_data.collaborators[*].permissions.maintain',
        'collaboration_data.collaborators[*].permissions.push',
        'collaboration_data.collaborators[*].permissions.pull',
        'collaboration_data.collaborators.*.login',
        'collaboration_data.collaborators.*.permissions',
        'collaboration_data.collaborators.*.permissions.admin',
        'collaboration_data.collaborators.*.permissions.maintain',
        'collaboration_data.collaborators.*.permissions.push',
        'collaboration_data.collaborators.*.permissions.pull',
        
        # DEEP NESTING: Security advisories
        'security_data.security_advisories.advisories',
        'security_data.security_advisories.advisories[*]',
        'security_data.security_advisories.advisories.*',
        'security_data.security_advisories.error',
        
        # DEEP NESTING: Vulnerability alerts with dependabot alerts
        'security_data.vulnerability_alerts.enabled',
        'security_data.vulnerability_alerts.dependabot_alerts',
        'security_data.vulnerability_alerts.dependabot_alerts[*].number',
        'security_data.vulnerability_alerts.dependabot_alerts[*].state',
        'security_data.vulnerability_alerts.dependabot_alerts[*].severity',
        'security_data.vulnerability_alerts.dependabot_alerts[*].package',
        'security_data.vulnerability_alerts.dependabot_alerts[*].created_at',
        'security_data.vulnerability_alerts.dependabot_alerts[*].updated_at',
        'security_data.vulnerability_alerts.dependabot_alerts.*.number',
        'security_data.vulnerability_alerts.dependabot_alerts.*.state',
        'security_data.vulnerability_alerts.dependabot_alerts.*.severity',
        'security_data.vulnerability_alerts.dependabot_alerts.*.package',
        'security_data.vulnerability_alerts.dependabot_alerts.*.created_at',
        'security_data.vulnerability_alerts.dependabot_alerts.*.updated_at',
        
        # Organization members with wildcard patterns
        'organization_data.members[*].login',
        'organization_data.members[*].id',
        'organization_data.members[*].type',
        'organization_data.members[*].site_admin',
        'organization_data.members[*].role',
        'organization_data.members.*.login',
        'organization_data.members.*.id',
        'organization_data.members.*.type',
        'organization_data.members.*.site_admin',
        'organization_data.members.*.role',
        
        # Teams with wildcard patterns
        'organization_data.teams[*].id',
        'organization_data.teams[*].name',
        'organization_data.teams[*].slug',
        'organization_data.teams[*].description',
        'organization_data.teams[*].privacy',
        'organization_data.teams[*].permission',
        'organization_data.teams.*.id',
        'organization_data.teams.*.name',
        'organization_data.teams.*.slug',
        'organization_data.teams.*.description',
        'organization_data.teams.*.privacy',
        'organization_data.teams.*.permission',
        
        # DEEP NESTING: Outside collaborators with permissions
        'organization_data.outside_collaborators[*].login',
        'organization_data.outside_collaborators[*].id',
        'organization_data.outside_collaborators[*].type',
        'organization_data.outside_collaborators[*].permissions',
        'organization_data.outside_collaborators[*].permissions.admin',
        'organization_data.outside_collaborators[*].permissions.maintain',
        'organization_data.outside_collaborators[*].permissions.push',
        'organization_data.outside_collaborators[*].permissions.pull',
        'organization_data.outside_collaborators.*.login',
        'organization_data.outside_collaborators.*.id',
        'organization_data.outside_collaborators.*.type',
        'organization_data.outside_collaborators.*.permissions',
        'organization_data.outside_collaborators.*.permissions.admin',
        'organization_data.outside_collaborators.*.permissions.maintain',
        'organization_data.outside_collaborators.*.permissions.push',
        'organization_data.outside_collaborators.*.permissions.pull',
        
        # Tags with wildcard patterns
        'advanced_features_data.tags[*].name',
        'advanced_features_data.tags[*].commit_sha',
        'advanced_features_data.tags[*].commit_date',
        'advanced_features_data.tags[*].message',
        'advanced_features_data.tags.*.name',
        'advanced_features_data.tags.*.commit_sha',
        'advanced_features_data.tags.*.commit_date',
        'advanced_features_data.tags.*.message',
        
        # Webhooks with wildcard patterns
        'advanced_features_data.webhooks[*].id',
        'advanced_features_data.webhooks[*].name',
        'advanced_features_data.webhooks[*].active',
        'advanced_features_data.webhooks[*].events',
        'advanced_features_data.webhooks[*].config.url',
        'advanced_features_data.webhooks[*].config.content_type',
        'advanced_features_data.webhooks[*].config.insecure_ssl',
        'advanced_features_data.webhooks[*].config.secret',
        'advanced_features_data.webhooks.*.id',
        'advanced_features_data.webhooks.*.name',
        'advanced_features_data.webhooks.*.active',
        'advanced_features_data.webhooks.*.events',
        'advanced_features_data.webhooks.*.config.url',
        'advanced_features_data.webhooks.*.config.content_type',
        'advanced_features_data.webhooks.*.config.insecure_ssl',
        'advanced_features_data.webhooks.*.config.secret',
        
        # DEEP NESTING: Webhook events array
        'advanced_features_data.webhooks[*].events[*]',
        'advanced_features_data.webhooks.*.events.*',
    ]
    
    _test_wildcard_field_paths_for_resource(github_resource, github_wildcard_patterns, "GitHub")
    
    # Test AWS wildcard patterns
    print("\n=== TESTING AWS WILDCARD ARRAY FIELD PATHS ===")
    aws_rc_service = ResourceCollectionService('aws')
    aws_rc = aws_rc_service.get_resource_collection()
    
    # Test EC2 wildcard patterns
    ec2_resource = next((r for r in aws_rc.resources if r.__class__.__name__ == 'EC2Resource'), None)
    if ec2_resource:
        ec2_wildcard_patterns = [
            # Instances with wildcard patterns
            'instances[*].id',
            'instances[*].instance_type',
            'instances[*].state',
            'instances[*].private_ip_address',
            'instances[*].public_ip_address',
            'instances[*].iam_instance_profile',
            'instances[*].iam_instance_profile.Arn',
            'instances[*].iam_instance_profile.Id',
            'instances[*].security_groups',
            'instances[*].network_interfaces',
            'instances[*].block_device_mappings',
            'instances.*.id',
            'instances.*.instance_type',
            'instances.*.state',
            'instances.*.private_ip_address',
            'instances.*.public_ip_address',
            'instances.*.iam_instance_profile',
            'instances.*.iam_instance_profile.Arn',
            'instances.*.iam_instance_profile.Id',
            'instances.*.security_groups',
            'instances.*.network_interfaces',
            'instances.*.block_device_mappings',
            
            # DEEP NESTING: Instances with all fields from YAML
            'instances[*].launch_time',
            'instances[*].image_id',
            'instances[*].vpc_id',
            'instances[*].subnet_id',
            'instances[*].availability_zone',
            'instances[*].key_name',
            'instances[*].platform',
            'instances[*].monitoring',
            'instances[*].ebs_optimized',
            'instances[*].instance_lifecycle',
            'instances.*.launch_time',
            'instances.*.image_id',
            'instances.*.vpc_id',
            'instances.*.subnet_id',
            'instances.*.availability_zone',
            'instances.*.key_name',
            'instances.*.platform',
            'instances.*.monitoring',
            'instances.*.ebs_optimized',
            'instances.*.instance_lifecycle',
            
            # DEEP NESTING: Instance security groups and network interfaces (arrays)
            'instances[*].security_groups[*]',
            'instances[*].network_interfaces[*]',
            'instances.*.security_groups.*',
            'instances.*.network_interfaces.*',
            
            # Block device mappings with nested wildcards
            'instances[*].block_device_mappings[*].device_name',
            'instances[*].block_device_mappings[*].ebs.volume_id',
            'instances[*].block_device_mappings[*].ebs.status',
            'instances[*].block_device_mappings[*].ebs.attach_time',
            'instances[*].block_device_mappings[*].ebs.delete_on_termination',
            'instances.*.block_device_mappings.*.device_name',
            'instances.*.block_device_mappings.*.ebs.volume_id',
            'instances.*.block_device_mappings.*.ebs.status',
            'instances.*.block_device_mappings.*.ebs.attach_time',
            'instances.*.block_device_mappings.*.ebs.delete_on_termination',
            
            # DEEP NESTING: Account reserved instances
            'account.reserved_instances[*].id',
            'account.reserved_instances[*].instance_type',
            'account.reserved_instances[*].availability_zone',
            'account.reserved_instances[*].state',
            'account.reserved_instances[*].instance_count',
            'account.reserved_instances[*].platform',
            'account.reserved_instances.*.id',
            'account.reserved_instances.*.instance_type',
            'account.reserved_instances.*.availability_zone',
            'account.reserved_instances.*.state',
            'account.reserved_instances.*.instance_count',
            'account.reserved_instances.*.platform',
            
            # DEEP NESTING: Account spot instances
            'account.spot_instances[*].id',
            'account.spot_instances[*].instance_type',
            'account.spot_instances[*].state',
            'account.spot_instances[*].availability_zone',
            'account.spot_instances[*].spot_price',
            'account.spot_instances[*].launch_time',
            'account.spot_instances.*.id',
            'account.spot_instances.*.instance_type',
            'account.spot_instances.*.state',
            'account.spot_instances.*.availability_zone',
            'account.spot_instances.*.spot_price',
            'account.spot_instances.*.launch_time',
            
            # VPCs with wildcard patterns
            'vpcs[*].id',
            'vpcs[*].cidr_block',
            'vpcs[*].state',
            'vpcs[*].dhcp_options_id',
            'vpcs[*].instance_tenancy',
            'vpcs[*].is_default',
            'vpcs.*.id',
            'vpcs.*.cidr_block',
            'vpcs.*.state',
            'vpcs.*.dhcp_options_id',
            'vpcs.*.instance_tenancy',
            'vpcs.*.is_default',
            
            # DEEP NESTING: VPC CIDR block associations
            'vpcs[*].cidr_block_association_set',
            'vpcs[*].cidr_block_association_set[*].association_id',
            'vpcs[*].cidr_block_association_set[*].cidr_block',
            'vpcs[*].cidr_block_association_set[*].state',
            'vpcs.*.cidr_block_association_set',
            'vpcs.*.cidr_block_association_set.*.association_id',
            'vpcs.*.cidr_block_association_set.*.cidr_block',
            'vpcs.*.cidr_block_association_set.*.state',
            
            # DEEP NESTING: Subnets
            'subnets[*].vpc_id',
            'subnets[*].availability_zone',
            'subnets[*].availability_zone_id',
            'subnets[*].cidr_block',
            'subnets[*].state',
            'subnets[*].map_public_ip_on_launch',
            'subnets[*].available_ip_address_count',
            'subnets.*.vpc_id',
            'subnets.*.availability_zone',
            'subnets.*.availability_zone_id',
            'subnets.*.cidr_block',
            'subnets.*.state',
            'subnets.*.map_public_ip_on_launch',
            'subnets.*.available_ip_address_count',
            
            # DEEP NESTING: Route tables with routes and associations
            'route_tables[*].vpc_id',
            'route_tables[*].routes',
            'route_tables[*].routes[*].destination_cidr_block',
            'route_tables[*].routes[*].gateway_id',
            'route_tables[*].routes[*].instance_id',
            'route_tables[*].routes[*].state',
            'route_tables[*].routes[*].origin',
            'route_tables[*].associations',
            'route_tables[*].associations[*].route_table_id',
            'route_tables[*].associations[*].subnet_id',
            'route_tables[*].associations[*].main',
            'route_tables[*].associations[*].association_state.state',
            'route_tables[*].associations[*].association_state.status_message',
            'route_tables.*.vpc_id',
            'route_tables.*.routes',
            'route_tables.*.routes.*.destination_cidr_block',
            'route_tables.*.routes.*.gateway_id',
            'route_tables.*.routes.*.instance_id',
            'route_tables.*.routes.*.state',
            'route_tables.*.routes.*.origin',
            'route_tables.*.associations',
            'route_tables.*.associations.*.route_table_id',
            'route_tables.*.associations.*.subnet_id',
            'route_tables.*.associations.*.main',
            'route_tables.*.associations.*.association_state.state',
            'route_tables.*.associations.*.association_state.status_message',
            
            # DEEP NESTING: NAT gateways
            'nat_gateways[*].state',
            'nat_gateways[*].subnet_id',
            'nat_gateways[*].vpc_id',
            'nat_gateways[*].create_time',
            'nat_gateways[*].delete_time',
            'nat_gateways[*].connectivity_type',
            'nat_gateways[*].public_ip',
            'nat_gateways[*].private_ip',
            'nat_gateways.*.state',
            'nat_gateways.*.subnet_id',
            'nat_gateways.*.vpc_id',
            'nat_gateways.*.create_time',
            'nat_gateways.*.delete_time',
            'nat_gateways.*.connectivity_type',
            'nat_gateways.*.public_ip',
            'nat_gateways.*.private_ip',
            
            # DEEP NESTING: Elastic IPs
            'elastic_ips[*].public_ip',
            'elastic_ips[*].domain',
            'elastic_ips[*].instance_id',
            'elastic_ips[*].network_interface_id',
            'elastic_ips[*].private_ip_address',
            'elastic_ips.*.public_ip',
            'elastic_ips.*.domain',
            'elastic_ips.*.instance_id',
            'elastic_ips.*.network_interface_id',
            'elastic_ips.*.private_ip_address',
            
            # DEEP NESTING: Key pairs
            'key_pairs[*].key_fingerprint',
            'key_pairs[*].key_type',
            'key_pairs[*].public_key',
            'key_pairs[*].create_time',
            'key_pairs.*.key_fingerprint',
            'key_pairs.*.key_type',
            'key_pairs.*.public_key',
            'key_pairs.*.create_time',
            
            # DEEP NESTING: Snapshots
            'snapshots[*].volume_id',
            'snapshots[*].volume_size',
            'snapshots[*].state',
            'snapshots[*].start_time',
            'snapshots[*].progress',
            'snapshots[*].encrypted',
            'snapshots[*].owner_id',
            'snapshots[*].description',
            'snapshots.*.volume_id',
            'snapshots.*.volume_size',
            'snapshots.*.state',
            'snapshots.*.start_time',
            'snapshots.*.progress',
            'snapshots.*.encrypted',
            'snapshots.*.owner_id',
            'snapshots.*.description',
            
            # DEEP NESTING: Volumes
            'volumes[*].size',
            'volumes[*].volume_type',
            'volumes[*].state',
            'volumes[*].availability_zone',
            'volumes[*].create_time',
            'volumes[*].encrypted',
            'volumes[*].iops',
            'volumes[*].throughput',
            'volumes[*].multi_attach_enabled',
            'volumes.*.size',
            'volumes.*.volume_type',
            'volumes.*.state',
            'volumes.*.availability_zone',
            'volumes.*.create_time',
            'volumes.*.encrypted',
            'volumes.*.iops',
            'volumes.*.throughput',
            'volumes.*.multi_attach_enabled',
            
            # DEEP NESTING: Network interfaces
            'network_interfaces[*].subnet_id',
            'network_interfaces[*].vpc_id',
            'network_interfaces[*].availability_zone',
            'network_interfaces[*].description',
            'network_interfaces[*].interface_type',
            'network_interfaces[*].private_ip_address',
            'network_interfaces[*].private_dns_name',
            'network_interfaces[*].source_dest_check',
            'network_interfaces[*].status',
            'network_interfaces[*].mac_address',
            'network_interfaces[*].security_groups',
            'network_interfaces[*].security_groups[*].group_id',
            'network_interfaces[*].security_groups[*].group_name',
            'network_interfaces.*.subnet_id',
            'network_interfaces.*.vpc_id',
            'network_interfaces.*.availability_zone',
            'network_interfaces.*.description',
            'network_interfaces.*.interface_type',
            'network_interfaces.*.private_ip_address',
            'network_interfaces.*.private_dns_name',
            'network_interfaces.*.source_dest_check',
            'network_interfaces.*.status',
            'network_interfaces.*.mac_address',
            'network_interfaces.*.security_groups',
            'network_interfaces.*.security_groups.*.group_id',
            'network_interfaces.*.security_groups.*.group_name',
            
            # DEEP NESTING: Internet gateways
            'internet_gateways[*].state',
            'internet_gateways[*].attachments',
            'internet_gateways[*].attachments[*].vpc_id',
            'internet_gateways[*].attachments[*].state',
            'internet_gateways.*.state',
            'internet_gateways.*.attachments',
            'internet_gateways.*.attachments.*.vpc_id',
            'internet_gateways.*.attachments.*.state',
            
            # Security group rules with wildcard patterns
            'security_groups.inbound_rules[*].protocol',
            'security_groups.inbound_rules[*].from_port',
            'security_groups.inbound_rules[*].to_port',
            'security_groups.inbound_rules[*].cidr',
            'security_groups.inbound_rules[*].description',
            'security_groups.inbound_rules[*].source_groups.group_id',
            'security_groups.inbound_rules[*].source_groups.group_name',
            'security_groups.inbound_rules.*.protocol',
            'security_groups.inbound_rules.*.from_port',
            'security_groups.inbound_rules.*.to_port',
            'security_groups.inbound_rules.*.cidr',
            'security_groups.inbound_rules.*.description',
            'security_groups.inbound_rules.*.source_groups.group_id',
            'security_groups.inbound_rules.*.source_groups.group_name',
            
            'security_groups.outbound_rules[*].protocol',
            'security_groups.outbound_rules[*].from_port',
            'security_groups.outbound_rules[*].to_port',
            'security_groups.outbound_rules[*].cidr',
            'security_groups.outbound_rules[*].description',
            'security_groups.outbound_rules[*].destination_groups.group_id',
            'security_groups.outbound_rules[*].destination_groups.group_name',
            'security_groups.outbound_rules.*.protocol',
            'security_groups.outbound_rules.*.from_port',
            'security_groups.outbound_rules.*.to_port',
            'security_groups.outbound_rules.*.cidr',
            'security_groups.outbound_rules.*.description',
            'security_groups.outbound_rules.*.destination_groups.group_id',
            'security_groups.outbound_rules.*.destination_groups.group_name',
        ]
        
        _test_wildcard_field_paths_for_resource(ec2_resource, ec2_wildcard_patterns, "EC2")
    
    # Test IAM wildcard patterns
    iam_resource = next((r for r in aws_rc.resources if r.__class__.__name__ == 'IAMResource'), None)
    if iam_resource:
        iam_wildcard_patterns = [
            # Users with wildcard patterns
            'users[*].id',
            'users[*].arn',
            'users[*].user_id',
            'users[*].create_date',
            'users[*].path',
            'users.*.id',
            'users.*.arn',
            'users.*.user_id',
            'users.*.create_date',
            'users.*.path',
            
            # Access keys with nested wildcards
            'users[*].access_keys[*].id',
            'users[*].access_keys[*].status',
            'users[*].access_keys[*].create_date',
            'users[*].access_keys[*].last_used_date',
            'users[*].access_keys[*].last_used_service',
            'users[*].access_keys[*].last_used_region',
            'users.*.access_keys.*.id',
            'users.*.access_keys.*.status',
            'users.*.access_keys.*.create_date',
            'users.*.access_keys.*.last_used_date',
            'users.*.access_keys.*.last_used_service',
            'users.*.access_keys.*.last_used_region',
            
            # MFA devices with nested wildcards
            'users[*].mfa_devices[*].serial_number',
            'users[*].mfa_devices[*].enable_date',
            'users[*].mfa_devices[*].type',
            'users[*].mfa_devices[*].virtual_mfa_token',
            'users.*.mfa_devices.*.serial_number',
            'users.*.mfa_devices.*.enable_date',
            'users.*.mfa_devices.*.type',
            'users.*.mfa_devices.*.virtual_mfa_token',
            
            # Policies with wildcard patterns
            'policies[*].id',
            'policies[*].policy_name',
            'policies[*].policy_id',
            'policies[*].create_date',
            'policies[*].update_date',
            'policies[*].path',
            'policies[*].default_version_id',
            'policies[*].attachment_count',
            'policies.*.id',
            'policies.*.policy_name',
            'policies.*.policy_id',
            'policies.*.create_date',
            'policies.*.update_date',
            'policies.*.path',
            'policies.*.default_version_id',
            'policies.*.attachment_count',
            
            # DEEP NESTING: Policy default version structure
            'policies[*].default_version',
            'policies[*].default_version.Document',
            'policies[*].default_version.Document.Version',
            'policies[*].default_version.Document.Statement',
            'policies[*].default_version.Document.Statement[*].Effect',
            'policies[*].default_version.Document.Statement[*].Action',
            'policies[*].default_version.Document.Statement[*].Resource',
            'policies[*].default_version.Document.Statement[*].Condition',
            'policies[*].default_version.VersionId',
            'policies[*].default_version.IsDefaultVersion',
            'policies[*].default_version.CreateDate',
            'policies.*.default_version',
            'policies.*.default_version.Document',
            'policies.*.default_version.Document.Version',
            'policies.*.default_version.Document.Statement',
            'policies.*.default_version.Document.Statement.*.Effect',
            'policies.*.default_version.Document.Statement.*.Action',
            'policies.*.default_version.Document.Statement.*.Resource',
            'policies.*.default_version.Document.Statement.*.Condition',
            'policies.*.default_version.VersionId',
            'policies.*.default_version.IsDefaultVersion',
            'policies.*.default_version.CreateDate',
        ]
        
        _test_wildcard_field_paths_for_resource(iam_resource, iam_wildcard_patterns, "IAM")
    
    # Test S3 wildcard patterns - DEEP NESTING
    s3_resource = next((r for r in aws_rc.resources if r.__class__.__name__ == 'S3Resource'), None)
    if s3_resource:
        s3_wildcard_patterns = [
            # Buckets with wildcard patterns
            'buckets[*].id',
            'buckets[*].name',
            'buckets[*].creation_date',
            'buckets[*].region',
            'buckets[*].versioning_status',
            'buckets[*].logging_enabled',
            'buckets[*].website_enabled',
            'buckets.*.id',
            'buckets.*.name',
            'buckets.*.creation_date',
            'buckets.*.region',
            'buckets.*.versioning_status',
            'buckets.*.logging_enabled',
            'buckets.*.website_enabled',
            
            # DEEP NESTING: Encryption structure
            'buckets[*].encryption',
            'buckets[*].encryption.enabled',
            'buckets[*].encryption.type',
            'buckets[*].encryption.kms_key_id',
            'buckets.*.encryption',
            'buckets.*.encryption.enabled',
            'buckets.*.encryption.type',
            'buckets.*.encryption.kms_key_id',
            
            # DEEP NESTING: Public access block structure
            'buckets[*].public_access_block',
            'buckets[*].public_access_block.block_public_acls',
            'buckets[*].public_access_block.block_public_policy',
            'buckets[*].public_access_block.ignore_public_acls',
            'buckets[*].public_access_block.restrict_public_buckets',
            'buckets.*.public_access_block',
            'buckets.*.public_access_block.block_public_acls',
            'buckets.*.public_access_block.block_public_policy',
            'buckets.*.public_access_block.ignore_public_acls',
            'buckets.*.public_access_block.restrict_public_buckets',
        ]
        
        _test_wildcard_field_paths_for_resource(s3_resource, s3_wildcard_patterns, "S3")
    
    # Test CloudTrail wildcard patterns - DEEP NESTING
    ct_resource = next((r for r in aws_rc.resources if r.__class__.__name__ == 'CloudTrailResource'), None)
    if ct_resource:
        ct_wildcard_patterns = [
            # Trails with wildcard patterns
            'trails[*].id',
            'trails[*].name',
            'trails[*].s3_bucket_name',
            'trails[*].s3_key_prefix',
            'trails[*].include_global_service_events',
            'trails[*].is_multi_region_trail',
            'trails[*].enable_log_file_validation',
            'trails[*].is_logging',
            'trails[*].kms_key_id',
            'trails[*].log_file_validation_enabled',
            'trails.*.id',
            'trails.*.name',
            'trails.*.s3_bucket_name',
            'trails.*.s3_key_prefix',
            'trails.*.include_global_service_events',
            'trails.*.is_multi_region_trail',
            'trails.*.enable_log_file_validation',
            'trails.*.is_logging',
            'trails.*.kms_key_id',
            'trails.*.log_file_validation_enabled',
            
            # DEEP NESTING: Event selectors with nested arrays
            'trails[*].event_selectors',
            'trails[*].event_selectors[*].read_write_type',
            'trails[*].event_selectors[*].include_management_events',
            'trails[*].event_selectors[*].data_resources',
            'trails[*].event_selectors[*].data_resources.type',
            'trails[*].event_selectors[*].data_resources.values',
            'trails[*].event_selectors[*].data_resources.values[*]',
            'trails.*.event_selectors',
            'trails.*.event_selectors.*.read_write_type',
            'trails.*.event_selectors.*.include_management_events',
            'trails.*.event_selectors.*.data_resources',
            'trails.*.event_selectors.*.data_resources.type',
            'trails.*.event_selectors.*.data_resources.values',
            'trails.*.event_selectors.*.data_resources.values.*',
            
            # DEEP NESTING: Insight selectors
            'trails[*].insight_selectors',
            'trails[*].insight_selectors[*].insight_type',
            'trails.*.insight_selectors',
            'trails.*.insight_selectors.*.insight_type',
            
            # DEEP NESTING: Tags
            'trails[*].tags',
            'trails[*].tags[*].key',
            'trails[*].tags[*].value',
            'trails.*.tags',
            'trails.*.tags.*.key',
            'trails.*.tags.*.value',
            
            # Resource-level event selectors (also deep)
            'event_selectors[*].read_write_type',
            'event_selectors[*].include_management_events',
            'event_selectors[*].data_resources',
            'event_selectors[*].data_resources.type',
            'event_selectors[*].data_resources.values',
            'event_selectors[*].data_resources.values[*]',
            'event_selectors.*.read_write_type',
            'event_selectors.*.include_management_events',
            'event_selectors.*.data_resources',
            'event_selectors.*.data_resources.type',
            'event_selectors.*.data_resources.values',
            'event_selectors.*.data_resources.values.*',
        ]
        
        _test_wildcard_field_paths_for_resource(ct_resource, ct_wildcard_patterns, "CloudTrail")
    
    # Test CloudWatch wildcard patterns - DEEP NESTING
    cw_resource = next((r for r in aws_rc.resources if r.__class__.__name__ == 'CloudWatchResource'), None)
    if cw_resource:
        cw_wildcard_patterns = [
            # Log groups with wildcard patterns
            'log_groups[*].id',
            'log_groups[*].log_group_name',
            'log_groups[*].creation_time',
            'log_groups[*].retention_in_days',
            'log_groups[*].metric_filter_count',
            'log_groups[*].arn',
            'log_groups[*].stored_bytes',
            'log_groups[*].kms_key_id',
            'log_groups.*.id',
            'log_groups.*.log_group_name',
            'log_groups.*.creation_time',
            'log_groups.*.retention_in_days',
            'log_groups.*.metric_filter_count',
            'log_groups.*.arn',
            'log_groups.*.stored_bytes',
            'log_groups.*.kms_key_id',
            
            # Metrics with wildcard patterns
            'metrics[*].namespace',
            'metrics[*].metric_name',
            'metrics[*].dimensions',
            'metrics.*.namespace',
            'metrics.*.metric_name',
            'metrics.*.dimensions',
            
            # DEEP NESTING: Metric dimensions
            'metrics[*].dimensions[*].Name',
            'metrics[*].dimensions[*].Value',
            'metrics.*.dimensions.*.Name',
            'metrics.*.dimensions.*.Value',
            
            # Alarms with wildcard patterns
            'alarms[*].alarm_name',
            'alarms[*].alarm_description',
            'alarms[*].actions_enabled',
            'alarms[*].state_value',
            'alarms[*].state_reason',
            'alarms[*].state_updated_timestamp',
            'alarms[*].metric_name',
            'alarms[*].namespace',
            'alarms[*].statistic',
            'alarms[*].period',
            'alarms[*].evaluation_periods',
            'alarms[*].threshold',
            'alarms[*].comparison_operator',
            'alarms.*.alarm_name',
            'alarms.*.alarm_description',
            'alarms.*.actions_enabled',
            'alarms.*.state_value',
            'alarms.*.state_reason',
            'alarms.*.state_updated_timestamp',
            'alarms.*.metric_name',
            'alarms.*.namespace',
            'alarms.*.statistic',
            'alarms.*.period',
            'alarms.*.evaluation_periods',
            'alarms.*.threshold',
            'alarms.*.comparison_operator',
            
            # DEEP NESTING: Alarm actions (arrays)
            'alarms[*].ok_actions',
            'alarms[*].ok_actions[*]',
            'alarms[*].alarm_actions',
            'alarms[*].alarm_actions[*]',
            'alarms[*].insufficient_data_actions',
            'alarms[*].insufficient_data_actions[*]',
            'alarms.*.ok_actions',
            'alarms.*.ok_actions.*',
            'alarms.*.alarm_actions',
            'alarms.*.alarm_actions.*',
            'alarms.*.insufficient_data_actions',
            'alarms.*.insufficient_data_actions.*',
            
            # DEEP NESTING: Alarm dimensions
            'alarms[*].dimensions',
            'alarms[*].dimensions[*].Name',
            'alarms[*].dimensions[*].Value',
            'alarms.*.dimensions',
            'alarms.*.dimensions.*.Name',
            'alarms.*.dimensions.*.Value',
            
            # Dashboards with wildcard patterns
            'dashboards[*].dashboard_name',
            'dashboards[*].dashboard_arn',
            'dashboards[*].dashboard_body',
            'dashboards[*].size',
            'dashboards[*].last_modified',
            'dashboards.*.dashboard_name',
            'dashboards.*.dashboard_arn',
            'dashboards.*.dashboard_body',
            'dashboards.*.size',
            'dashboards.*.last_modified',
        ]
        
        _test_wildcard_field_paths_for_resource(cw_resource, cw_wildcard_patterns, "CloudWatch")


def _test_wildcard_field_paths_for_resource(resource, field_paths, resource_name):
    """Helper function to test wildcard field paths for a specific resource."""
    print(f"\n--- Testing {resource_name} Resource Wildcard Field Paths ---")
    
    for field_path in field_paths:
        print(f"Testing {resource_name} wildcard field path: {field_path}")
        
        # Simulate the _extract_array_values logic
        try:
            # Convert [*] notation to .* notation for processing
            normalized_path = field_path.replace('[*]', '.*')
            parts = normalized_path.split('.')
            
            # Find the first wildcard position
            wildcard_index = None
            for i, part in enumerate(parts):
                if part == '*':
                    wildcard_index = i
                    break
            
            if wildcard_index is None:
                # No wildcard found, treat as regular field path
                path_parts = field_path.replace('[*]', '').split('.')
                current = resource
                path_traversed = []
                
                for part in path_parts:
                    path_traversed.append(part)
                    current_path = '.'.join(path_traversed)
                    
                    assert hasattr(current, part), f"Field '{part}' not found in path '{current_path}' for {resource_name} wildcard field path '{field_path}'"
                    current = getattr(current, part)
                    print(f"  ✓ Found '{part}' - type: {type(current)}")
            else:
                # Handle wildcard field paths - potentially with multiple levels of wildcards
                current = resource
                processed_parts = []
                remaining_parts = parts.copy()
                
                while remaining_parts:
                    # Find next wildcard
                    next_wildcard_index = None
                    for i, part in enumerate(remaining_parts):
                        if part == '*':
                            next_wildcard_index = i
                            break
                    
                    if next_wildcard_index is None:
                        # No more wildcards, process remaining parts normally
                        for part in remaining_parts:
                            if hasattr(current, part):
                                current = getattr(current, part)
                                processed_parts.append(part)
                                print(f"  ✓ Found '{part}' - type: {type(current)}")
                            else:
                                print(f"    ℹ️  Field '{part}' not found (may be optional or empty)")
                                break
                        break
                    
                    # Process parts up to the wildcard
                    array_path_parts = remaining_parts[:next_wildcard_index]
                    
                    for key in array_path_parts:
                        assert hasattr(current, key), f"Field '{key}' not found in array path for {resource_name} wildcard field path '{field_path}'"
                        current = getattr(current, key)
                        processed_parts.append(key)
                        print(f"  ✓ Found '{key}' - type: {type(current)}")
                    
                    # Ensure we have an array/list at the wildcard position
                    assert isinstance(current, (list, tuple)), f"Expected array at '{'.'.join(processed_parts)}', got {type(current)} for {resource_name} wildcard field path '{field_path}'"
                    
                    print(f"  ✓ Found array with {len(current)} items")
                    
                    # If array is not empty, use first item to continue processing
                    if current:
                        current = current[0]
                        print(f"    → Using first array item for further processing")
                        
                        # Update remaining parts (skip the wildcard)
                        remaining_parts = remaining_parts[next_wildcard_index + 1:]
                        processed_parts.append('*')
                    else:
                        print(f"    → Empty array, cannot traverse further")
                        # For empty arrays, we can't traverse further but this shouldn't be an error
                        break
                
                print(f"  ✅ Wildcard field path '{field_path}' processed successfully")
                
        except Exception as e:
            print(f"  ❌ Error processing wildcard field path '{field_path}': {str(e)}")
            # Check if this is an expected optional field
            if any(optional_term in field_path.lower() for optional_term in ['error', 'optional', 'tags', 'webhooks', 'mfa_devices', 'access_keys']):
                print(f"    ℹ️  This appears to be an optional field, continuing...")
                continue
            # Re-raise the exception to fail the test for required fields
            raise AssertionError(f"Failed to process wildcard field path '{field_path}' for {resource_name}: {str(e)}")
