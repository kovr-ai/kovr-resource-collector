"""Tests for verifying YAML schema to JSON data mapping."""
from typing import List

from con_mon_v2.utils.services import ResourceCollectionService
from con_mon_v2.resources import ResourceCollection
from con_mon_v2.compliance.models import (
    Check, CheckMetadata, OutputStatements, FixDetails,
    CheckOperation, ComparisonOperationEnum, CheckResult
)
from datetime import datetime


def setup_github_resource_service() -> ResourceCollection:
    rc_service = ResourceCollectionService('github')
    return rc_service.get_resource_collection()


def setup_aws_resource_service() -> ResourceCollection:
    rc_service = ResourceCollectionService('aws')
    return rc_service.get_resource_collection()


def setup_test_check() -> Check:

    metadata = CheckMetadata(
        operation=CheckOperation(name=ComparisonOperationEnum.CUSTOM, logic="result = True"),
        field_path="test.path",
        resource_type="con_mon_v2.mappings.github.GithubResource",
        tags=["test"],
        category="test",
        severity="medium",
        expected_value=None
    )

    check = Check(
        id="test_functions",
        name="Functions Test Check",
        description="Test function extraction",
        category="test",
        created_by="test",
        updated_by="test",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        metadata=metadata,
        output_statements=OutputStatements(
            success="Test passed", failure="Test failed", partial="Test partial"
        ),
        fix_details=FixDetails(
            description="Test fix",
            instructions=["Step 1"],
            automation_available=False,
            estimated_time="1 w 1 d 1 h"
        ),
        is_deleted=False
    )
    return check.model_copy()


def list_of_field_paths(resource_name) -> List[str]:
    field_paths = {
        'GithubResource': [
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
            # Metadata arrays
            'repository_data.metadata.topics[]',

            # Branches arrays
            'repository_data.branches[].name',
            'repository_data.branches[].sha',
            'repository_data.branches[].protected',
            'repository_data.branches[].protection_details.required_status_checks',
            'repository_data.branches[].protection_details.enforce_admins',
            'repository_data.branches[].protection_details.required_pull_request_reviews',
            'repository_data.branches[].protection_details.restrictions',

            # Statistics arrays
            'repository_data.statistics.code_frequency[].timestamp',
            'repository_data.statistics.code_frequency[].additions',
            'repository_data.statistics.code_frequency[].deletions',

            # Actions arrays
            'actions_data.workflows.recent_runs[].id',
            'actions_data.workflows.recent_runs[].name',
            'actions_data.workflows.recent_runs[].head_branch',
            'actions_data.workflows.recent_runs[].status',
            'actions_data.workflows.recent_runs[].conclusion',

            # Collaboration arrays
            'collaboration_data.issues[].number',
            'collaboration_data.issues[].title',
            'collaboration_data.issues[].state',
            'collaboration_data.issues[].user',
            'collaboration_data.pull_requests[].number',
            'collaboration_data.pull_requests[].title',
            'collaboration_data.pull_requests[].state',
            'collaboration_data.pull_requests[].user',
            'collaboration_data.collaborators[].login',
            'collaboration_data.collaborators[].permissions.admin',

            # Organization arrays
            'organization_data.members[].login',
            'organization_data.members[].id',
            'organization_data.members[].role',
            'organization_data.teams[].id',
            'organization_data.teams[].name',
            'organization_data.teams[].privacy',
            'organization_data.outside_collaborators[].login',
            'organization_data.outside_collaborators[].permissions.admin',

            # Advanced features arrays
            'advanced_features_data.tags[].name',
            'advanced_features_data.tags[].commit_sha',
            'advanced_features_data.webhooks[].id',
            'advanced_features_data.webhooks[].name',
            'advanced_features_data.webhooks[].active',
            'advanced_features_data.webhooks[].events[]',
            'advanced_features_data.webhooks[].config.url',

            # Security arrays
            'security_data.security_advisories.advisories[]',
            'security_data.vulnerability_alerts.dependabot_alerts[].number',
            'security_data.vulnerability_alerts.dependabot_alerts[].state',
            'security_data.vulnerability_alerts.dependabot_alerts[].severity',

            # Basic function paths
            'len(repository_data.branches)',
            'len(collaboration_data.issues)',
            'len(collaboration_data.pull_requests)',
            'len(collaboration_data.collaborators)',
            'len(organization_data.members)',
            'len(organization_data.teams)',
            'len(advanced_features_data.tags)',
            'len(advanced_features_data.webhooks)',

            # any() function paths - the main question!
            'any(repository_data.branches.*.protected)',
            'any(collaboration_data.collaborators.*.permissions.admin)',
            'any(organization_data.members.*.site_admin)',
            'any(advanced_features_data.webhooks.*.active)',
            'any(security_data.vulnerability_alerts.dependabot_alerts.*.state)',

            # all() function paths
            'all(repository_data.branches.*.protected)',
            'all(collaboration_data.collaborators.*.permissions.admin)',
            'all(organization_data.members.*.site_admin)',
            'all(advanced_features_data.webhooks.*.active)',

            # count() function paths
            'count(repository_data.branches.*.protected)',
            'count(collaboration_data.collaborators.*.permissions.admin)',
            'count(organization_data.members.*.site_admin)',
            'count(advanced_features_data.webhooks.*.active)',

            # sum() function paths (for numeric values)
            'sum(repository_data.statistics.code_frequency.*.additions)',
            'sum(repository_data.statistics.code_frequency.*.deletions)',

            # max/min function paths (for numeric values)
            'max(repository_data.statistics.code_frequency.*.additions)',
            'min(repository_data.statistics.code_frequency.*.deletions)',
        ],

        'EC2Resource': [
            'instances[].iam_instance_profile',
            'instances[].iam_instance_profile.Arn',
            'instances[].iam_instance_profile.Id',
            'instances[].security_groups',
            'instances[].network_interfaces',
            'instances[].block_device_mappings',
            'instances[].block_device_mappings[].device_name',
            'instances[].block_device_mappings[].ebs',
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

            # Internet gateways
            'internet_gateways',
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

            # Account arrays
            'account.reserved_instances[].id',
            'account.reserved_instances[].instance_type',
            'account.reserved_instances[].availability_zone',
            'account.reserved_instances[].state',
            'account.reserved_instances[].instance_count',
            'account.reserved_instances[].platform',
            'account.spot_instances[].id',
            'account.spot_instances[].instance_type',
            'account.spot_instances[].state',
            'account.spot_instances[].availability_zone',
            'account.spot_instances[].spot_price',
            'account.spot_instances[].launch_time',

            # VPCs arrays
            'vpcs[].id',
            'vpcs[].cidr_block',
            'vpcs[].state',
            'vpcs[].dhcp_options_id',
            'vpcs[].instance_tenancy',
            'vpcs[].is_default',
            'vpcs[].cidr_block_association_set[].association_id',
            'vpcs[].cidr_block_association_set[].cidr_block',
            'vpcs[].cidr_block_association_set[].state',

            # Subnets arrays
            'subnets[].vpc_id',
            'subnets[].availability_zone',
            'subnets[].availability_zone_id',
            'subnets[].cidr_block',
            'subnets[].state',
            'subnets[].map_public_ip_on_launch',
            'subnets[].available_ip_address_count',

            # Route tables arrays
            'route_tables[].vpc_id',
            'route_tables[].routes[].destination_cidr_block',
            'route_tables[].routes[].gateway_id',
            'route_tables[].routes[].instance_id',
            'route_tables[].routes[].state',
            'route_tables[].routes[].origin',
            'route_tables[].associations[].route_table_id',
            'route_tables[].associations[].subnet_id',
            'route_tables[].associations[].main',
            'route_tables[].associations[].association_state.state',
            'route_tables[].associations[].association_state.status_message',

            # Other arrays
            'nat_gateways[].state',
            'nat_gateways[].subnet_id',
            'nat_gateways[].vpc_id',
            'elastic_ips[].public_ip',
            'elastic_ips[].domain',
            'elastic_ips[].instance_id',
            'key_pairs[].key_fingerprint',
            'key_pairs[].key_type',
            'snapshots[].volume_id',
            'snapshots[].state',
            'volumes[].size',
            'volumes[].volume_type',
            'volumes[].state',
            'network_interfaces[].subnet_id',
            'network_interfaces[].vpc_id',
            'network_interfaces[].security_groups[].group_id',
            'network_interfaces[].security_groups[].group_name',
            'internet_gateways[].state',
            'internet_gateways[].attachments[].vpc_id',
            'internet_gateways[].attachments[].state',
            # Basic AWS function paths
            'len(instances)',
            'len(vpcs)',
            'len(subnets)',
            'len(security_groups.inbound_rules)',
            'len(security_groups.outbound_rules)',

            # any() function paths for AWS
            'any(instances.*.ebs_optimized)',
            'any(vpcs.*.is_default)',
            'any(volumes.*.encrypted)',
            'any(snapshots.*.encrypted)',

            # count() function paths for AWS
            'count(instances.*.ebs_optimized)',
            'count(vpcs.*.is_default)',
            'count(volumes.*.encrypted)',
        ],

        'IAMResource': [
            'id',
            'users',
            'policies',
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
            'policies[].default_version.Document.Statement[].Effect',
            'policies[].default_version.Document.Statement[].Action',
            'policies[].default_version.Document.Statement[].Resource',
            'policies[].default_version.Document.Statement[].Condition',
            'policies[].default_version.VersionId',
            'policies[].default_version.IsDefaultVersion',
            'policies[].default_version.CreateDate',
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
        ],

        'S3Resource': [
            'id',
            'buckets',
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
        ],

        'CloudTrailResource': [
            'id',
            'trails',
            'event_selectors',
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
            'trails[].event_selectors[].data_resources.values[]',
            'trails[].insight_selectors',
            'trails[].insight_selectors[].insight_type',
            'trails[].is_logging',
            'trails[].kms_key_id',
            'trails[].log_file_validation_enabled',
            'trails[].tags',
            'trails[].tags[].key',
            'trails[].tags[].value',

            # Resource-level event selectors
            'event_selectors[].read_write_type',
            'event_selectors[].include_management_events',
            'event_selectors[].data_resources.type',
            'event_selectors[].data_resources.values',
            'event_selectors[].data_resources.values[]',

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
        ],

        'CloudWatchResource': [
            'id',
            'log_groups',
            'metrics',
            'alarms',
            'dashboards',
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
            'metrics[].dimensions[].Name',
            'metrics[].dimensions[].Value',
            'alarms[].alarm_name',
            'alarms[].alarm_description',
            'alarms[].actions_enabled',
            'alarms[].ok_actions',
            'alarms[].ok_actions[]',
            'alarms[].alarm_actions',
            'alarms[].alarm_actions[]',
            'alarms[].insufficient_data_actions',
            'alarms[].insufficient_data_actions[]',
            'alarms[].state_value',
            'alarms[].state_reason',
            'alarms[].state_updated_timestamp',
            'alarms[].metric_name',
            'alarms[].namespace',
            'alarms[].statistic',
            'alarms[].dimensions',
            'alarms[].dimensions[].Name',
            'alarms[].dimensions[].Value',
            'alarms[].period',
            'alarms[].evaluation_periods',
            'alarms[].threshold',
            'alarms[].comparison_operator',
            'dashboards[].dashboard_name',
            'dashboards[].dashboard_arn',
            'dashboards[].dashboard_body',
            'dashboards[].size',
            'dashboards[].last_modified',

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
    }
    return field_paths[resource_name]


def check_is_invalid(check: Check, check_results: List[CheckResult]) -> bool:
    """
    Validate based on any errors in check results if check should be used in production.
    Return True if check is invalid and should be regenerated.

    A check is considered invalid if:
    1. No results available (can't evaluate)
    2. All results have passed=None (evaluation errors/exceptions)
    3. There are critical errors that prevent proper evaluation

    A check is considered VALID (should not be regenerated) if:
    1. At least one result has passed=True or passed=False (successful evaluation)
    2. The check logic executed properly, even if it failed compliance

    Args:
        check_results: List of CheckResult objects from evaluating the check

    Returns:
        bool: True if check is invalid and should be regenerated, False if acceptable
    """
    print(f"🔍 check_is_invalid called with {len(check_results) if check_results else 0} results")

    if not check_results:
        print("❌ No check results - considering invalid")
        return True

    check_results = [
        check_result
        for check_result in check_results
        if check_result.resource_model == check.resource_model
    ]
    if not check_results:
        return False
    # Debug: Print all results
    for i, result in enumerate(check_results):
        print(f"   Result {i + 1}: passed={result.passed}, error={result.error}")

    # Count results with actual boolean values (successful evaluations)
    successful_evaluations = 0
    error_evaluations = 0

    for check_result in check_results:
        if check_result.passed is not None:  # Either True or False
            successful_evaluations += 1
            print(f"   ✅ Successful evaluation: passed={check_result.passed}")
        else:
            error_evaluations += 1
            print(f"   ❌ Error evaluation: passed=None, error={check_result.error}")

    # Check is VALID if we have at least some successful evaluations
    # Even if all evaluations failed (passed=False), the check logic worked
    if successful_evaluations > 0:
        print(f"✅ Check has {successful_evaluations} successful evaluations - considering VALID")
        print("   (Check logic executed properly, even if compliance failed)")
        return False

    # Check is INVALID if all evaluations failed with errors
    print(f"❌ All {error_evaluations} evaluations had errors (passed=None) - considering INVALID")
    print("   (Check logic has fundamental issues and needs regeneration)")
    return True


def test_github_resource_collection():
    rc = setup_github_resource_service()
    check = setup_test_check()
    for resource in rc.resources:
        resource_name = resource.__class__.__name__
        for field_path in list_of_field_paths(resource_name):
            check.metadata.field_path = field_path
            check_results = check.evaluate(rc.resources)
            assert check_is_invalid(check, check_results) is False, f'Check Evaluation failed for {resource_name}.{field_path}'

def test_aws_resource_collection():
    rc = setup_aws_resource_service()
    check = setup_test_check()
    for resource in rc.resources:
        resource_name = resource.__class__.__name__
        for field_path in list_of_field_paths(resource_name):
            check.metadata.field_path = field_path
            check_results = check.evaluate(rc.resources)
            assert check_is_invalid(check, check_results) is False, f'Check Evaluation failed for {resource_name}.{field_path}'


if __name__ == '__main__':
    test_github_resource_collection()
    test_aws_resource_collection()
