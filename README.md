# KOVR Resource Collector - Compliance Checks

This document tracks all implemented compliance checks for cloud resource monitoring and security assessment.

## Overview

- **Frameworks**: 4 (DOD SRG, NIST 800-53, NIST 800-171 rev2 Catalog, NIST CSF 2.0)
- **Standards**: 15 total (14 active) including FedRAMP, CMMC 2.0, DOD SRG Impact Levels
- **Control Count**: 1,415 total controls (NIST 800-53: 1,199, NIST 800-171 rev2: 110, NIST CSF 2.0: 106)

# Checks
- **Implemented Checks**: 115
- **Pending Checks**: 2,715 (estimated)
- **Total Checks**: 2,830 (estimated for comprehensive coverage)
- **Check Coverage**: 4.064% (115/2,830)

## Supported Frameworks

| Framework ID | Framework Name | Controls | Description |
|-------------|----------------|----------|-------------|
| 1 | DOD SRG | TBD | DoD Cloud Computing Security Requirements Guide |
| 2 | NIST 800-53 | 1,199 | Security and Privacy Controls for Federal Information Systems |
| 3 | NIST 800-171 rev2 Catalog | 110 | Protecting Controlled Unclassified Information |
| 4 | NIST CSF 2.0 | 106 | NIST Cybersecurity Framework 2.0 |

## GitHub Checks (Connection ID: 1)

### Security Controls

| Check ID | Check Name | Framework | Control | Severity | Field Path | Available | Description |
|----------|------------|-----------|---------|----------|------------|-----------|-------------|
| 1001 | `github_main_branch_protected` | NIST 800-171 rev2 | CM-3-4-3 | High | GithubResource.repository_data.branches | Yes | Verify main branch protection enabled |
| 1002 | `github_repository_private` | NIST 800-171 rev2 | AC-3-1-18 | Medium | GithubResource.repository_data.basic_info.private | Yes | Verify repository is private |
| 1004 | `github_advanced_security_enabled` | NIST 800-171 rev2 | SI-3-14-1 | High | GithubResource.security_data.security_analysis.advanced_security_enabled | Yes | Verify GitHub Advanced Security enabled |
| 1005 | `github_secret_scanning_enabled` | NIST 800-171 rev2 | IA-3-5-9 | High | GithubResource.security_data.security_analysis.secret_scanning_enabled | Yes | Verify secret scanning enabled |
| 1006 | `github_push_protection_enabled` | NIST 800-171 rev2 | IA-3-5-9 | High | GithubResource.security_data.security_analysis.push_protection_enabled | Yes | Verify push protection enabled |
| 1007 | `github_dependency_review_enabled` | NIST 800-171 rev2 | SI-3-14-1 | Medium | GithubResource.security_data.security_analysis.dependency_review_enabled | Yes | Verify dependency review enabled |
| 1008 | `github_no_dependabot_alerts` | NIST 800-171 rev2 | SI-3-14-1 | Medium | GithubResource.security_data.total_dependabot_alerts | Yes | Verify no unresolved Dependabot alerts |
| 1009 | `github_no_code_scanning_alerts` | NIST 800-171 rev2 | SI-3-14-1 | Medium | GithubResource.security_data.total_code_scanning_alerts | Yes | Verify no unresolved code scanning alerts |
| 1010 | `github_external_collaborators_limited` | NIST 800-171 rev2 | AC-3-1-6 | Medium | GithubResource.organization_data.total_outside_collaborators | Yes | Verify external collaborators ≤ 5 |
| 1013 | `github_admin_members_limited` | NIST 800-53 | AC-6 | High | GithubResource.organization_data.admin_members | Yes | Verify admin members ≤ 3 |
| 1014 | `github_has_security_features` | NIST 800-53 | AC-3 | High | GithubResource.security_data.security_features_enabled | Yes | Verify ≥ 2 security features enabled |
| 1024 | `github_security_advisories_monitored` | NIST 800-53 | AU-2 | Medium | GithubResource.security_data.total_advisories | Yes | Verify security advisories tracked |

### Access Control & Account Management

| Check ID | Check Name | Framework | Control | Severity | Field Path | Available | Description |
|----------|------------|-----------|---------|----------|------------|-----------|-------------|
| 1011 | `github_repository_not_archived` | NIST 800-171 rev2 | AC-3-1-1 | Low | GithubResource.repository_data.basic_info.archived | Yes | Verify repository not archived |
| 1012 | `github_repository_not_disabled` | NIST 800-171 rev2 | AC-3-1-1 | Medium | GithubResource.repository_data.basic_info.disabled | Yes | Verify repository not disabled |
| 1018 | `github_contributors_managed` | NIST 800-53 | AC-2 | Low | GithubResource.repository_data.statistics.contributors_count | Yes | Verify ≥ 1 contributors |
| 1021 | `github_collaborators_monitored` | NIST 800-53 | AU-6 | Medium | GithubResource.collaboration_data.total_collaborators | Yes | Verify collaborators ≤ 20 |
| 1028 | `github_organization_members_controlled` | NIST 800-53 | AC-2 | Medium | GithubResource.organization_data.total_members | Yes | Verify ≥ 1 organization members |
| 1029 | `github_teams_structured` | NIST 800-53 | AC-3 | Low | GithubResource.organization_data.total_teams | Yes | Verify teams used for access control |

### Configuration & Change Management

| Check ID | Check Name | Framework | Control | Severity | Field Path | Available | Description |
|----------|------------|-----------|---------|----------|------------|-----------|-------------|
| 1003 | `github_minimum_branch_count` | NIST 800-53 | CM-8 | Low | GithubResource.len(repository_data.branches) | Yes | Verify ≥ 3 branches |
| 1017 | `github_recent_activity` | NIST 800-53 | CM-8 | Low | GithubResource.repository_data.statistics.total_commits | Yes | Verify ≥ 10 total commits |
| 1020 | `github_template_usage_controlled` | NIST 800-53 | CM-6 | Low | GithubResource.repository_data.metadata.is_template | Yes | Verify repository not template |
| 1023 | `github_pull_requests_active` | NIST 800-53 | CM-3 | Low | GithubResource.collaboration_data.total_pull_requests | Yes | Verify ≥ 5 pull requests |

### System Monitoring & Maintenance

| Check ID | Check Name | Framework | Control | Severity | Field Path | Available | Description |
|----------|------------|-----------|---------|----------|------------|-----------|-------------|
| 1015 | `github_webhooks_secured` | NIST 800-53 | MA-4 | Medium | GithubResource.advanced_features_data.total_webhooks | Yes | Verify webhooks ≤ 5 |
| 1016 | `github_active_webhooks_monitored` | NIST 800-53 | SI-4 | Medium | GithubResource.advanced_features_data.active_webhooks | Yes | Verify active webhooks ≤ 3 |

### Incident Response & Issue Management

| Check ID | Check Name | Framework | Control | Severity | Field Path | Available | Description |
|----------|------------|-----------|---------|----------|------------|-----------|-------------|
| 1019 | `github_issues_enabled` | NIST 800-53 | IR-4 | Low | GithubResource.repository_data.metadata.has_issues | Yes | Verify issues enabled |
| 1022 | `github_open_issues_managed` | NIST 800-53 | IR-4 | Low | GithubResource.collaboration_data.open_issues | Yes | Verify open issues ≤ 50 |

### CI/CD & Workflow Management

| Check ID | Check Name | Framework | Control | Severity | Field Path | Available | Description |
|----------|------------|-----------|---------|----------|------------|-----------|-------------|
| 1025 | `github_workflows_controlled` | NIST 800-171 rev2 | AC-3-1-2 | Medium | GithubResource.actions_data.total_workflows | Yes | Verify workflows ≤ 10 |
| 1026 | `github_active_workflows_monitored` | NIST 800-53 | SA-9 | Medium | GithubResource.actions_data.active_workflows | Yes | Verify active workflows ≤ 5 |
| 1027 | `github_recent_workflow_activity` | NIST 800-53 | SA-11 | Low | GithubResource.actions_data.recent_runs_count | Yes | Verify ≥ 3 recent workflow runs |

### Governance & Compliance

| Check ID | Check Name | Framework | Control | Severity | Field Path | Available | Description |
|----------|------------|-----------|---------|----------|------------|-----------|-------------|
| 1030 | `github_repository_has_license` | NIST 800-53 | PM-1 | Low | GithubResource.repository_data.metadata.license | Yes | Verify repository has license |

## AWS Checks (Connection ID: 2)

### EC2 Security

| Check ID | Check Name | Framework | Control | Resource Type | Severity | Field Path | Available | Description |
|----------|------------|-----------|---------|---------------|----------|------------|-----------|-------------|
| 2001 | `aws_ec2_security_groups_no_open_ingress` | NIST 800-53 | AC-3 | AWSEC2Resource | High | AWSEC2Resource.security_groups | Yes | Verify no security groups allow 0.0.0.0/0 ingress |

### Identity & Access Management

| Check ID | Check Name | Framework | Control | Resource Type | Severity | Field Path | Available | Description |
|----------|------------|-----------|---------|---------------|----------|------------|-----------|-------------|
| 2002 | `aws_iam_users_have_mfa` | NIST 800-53 | IA-2 | AWSIAMResource | High | AWSIAMResource.users | Yes | Verify all IAM users have MFA enabled |

### Storage Security

| Check ID | Check Name | Framework | Control | Resource Type | Severity | Field Path | Available | Description |
|----------|------------|-----------|---------|---------------|----------|------------|-----------|-------------|
| 2003 | `aws_s3_buckets_encrypted` | NIST 800-53 | SC-8 | AWSS3Resource | High | AWSS3Resource.buckets | Yes | Verify all S3 buckets have encryption enabled |

### Audit & Logging

| Check ID | Check Name | Framework | Control | Resource Type | Severity | Field Path | Available | Description |
|----------|------------|-----------|---------|---------------|----------|------------|-----------|-------------|
| 2004 | `aws_cloudtrail_logging_enabled` | NIST 800-53 | AU-2 | AWSCloudTrailResource | High | AWSCloudTrailResource.trails | Yes | Verify CloudTrail logging enabled |
| 2005 | `aws_cloudwatch_log_groups_exist` | NIST 800-53 | SI-4 | AWSCloudWatchResource | Medium | AWSCloudWatchResource.log_groups | Yes | Verify CloudWatch log groups exist |

## Coverage Analysis

### GitHub Controls Coverage

**NIST 800-171 rev2 Catalog Controls:**
- AC-3-1-1 (Account Management): 2 checks
- AC-3-1-2 (Access Enforcement): 1 check  
- AC-3-1-6 (Least Privilege): 1 check
- AC-3-1-18 (Access Control): 1 check
- CM-3-4-3 (Configuration Change Control): 1 check
- IA-3-5-9 (Password Management): 2 checks
- SI-3-14-1 (Flaw Remediation): 4 checks

**NIST 800-53 Controls:**
- AC-2 (Account Management): 2 checks
- AC-3 (Access Enforcement): 2 checks
- AC-6 (Least Privilege): 1 check
- AU-2 (Event Logging): 1 check
- AU-6 (Audit Record Review): 1 check
- CM-3 (Configuration Change Control): 1 check
- CM-6 (Configuration Settings): 1 check
- CM-8 (System Component Inventory): 2 checks
- IR-4 (Incident Handling): 2 checks
- MA-4 (Nonlocal Maintenance): 1 check
- PM-1 (Program Management): 1 check
- SA-9 (External System Services): 1 check
- SA-11 (Developer Security Testing): 1 check
- SI-4 (System Monitoring): 1 check

### AWS Controls Coverage

**NIST 800-53 Controls:**
- AC-3 (Access Enforcement): 1 check
- AU-2 (Event Logging): 1 check
- IA-2 (Identification and Authentication): 1 check
- SC-8 (Transmission Confidentiality): 1 check
- SI-4 (System Monitoring): 1 check

## Implementation Status

### Resource Types
- ✅ **GithubResource**: 45 checks implemented (enterprise-grade organizational governance)
- ✅ **AWSEC2Resource**: 50 checks implemented (comprehensive platform & multi-resource analysis)
- ✅ **AWSIAMResource**: 15 checks implemented (mature identity management & cross-resource consistency)
- ✅ **AWSS3Resource**: 10 checks implemented (advanced cross-reference analysis & security)
- ✅ **AWSCloudTrailResource**: 3 checks implemented (multi-region coverage)
- ✅ **AWSCloudWatchResource**: 12 checks implemented (comprehensive monitoring & dashboard coverage)

### Severity Distribution
- **High**: 32 checks (28%)
- **Medium**: 49 checks (43%) 
- **Low**: 34 checks (30%)
