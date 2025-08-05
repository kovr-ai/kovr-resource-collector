# KOVR Resource Collector - Compliance Checks

This document tracks all implemented compliance checks for cloud resource monitoring and security assessment.

## Overview

- **Total Checks**: 35
- **GitHub Checks**: 30 (covering 21 unique controls)
- **AWS Checks**: 5 (covering 5 unique controls)
- **Frameworks**: NIST 800-53, NIST 800-171 rev2 Catalog

## Supported Frameworks

| Framework ID | Framework Name | Description |
|-------------|----------------|-------------|
| 2 | NIST 800-53 | Security and Privacy Controls for Federal Information Systems |
| 3 | NIST 800-171 rev2 Catalog | Protecting Controlled Unclassified Information |

## GitHub Checks (Connection ID: 1)

### Security Controls

| Check ID | Check Name | Framework | Control | Severity | Description |
|----------|------------|-----------|---------|----------|-------------|
| 1001 | `github_main_branch_protected` | NIST 800-171 rev2 | CM-3-4-3 | High | Verify main branch protection enabled |
| 1002 | `github_repository_private` | NIST 800-171 rev2 | AC-3-1-18 | Medium | Verify repository is private |
| 1004 | `github_advanced_security_enabled` | NIST 800-171 rev2 | SI-3-14-1 | High | Verify GitHub Advanced Security enabled |
| 1005 | `github_secret_scanning_enabled` | NIST 800-171 rev2 | IA-3-5-9 | High | Verify secret scanning enabled |
| 1006 | `github_push_protection_enabled` | NIST 800-171 rev2 | IA-3-5-9 | High | Verify push protection enabled |
| 1007 | `github_dependency_review_enabled` | NIST 800-171 rev2 | SI-3-14-1 | Medium | Verify dependency review enabled |
| 1008 | `github_no_dependabot_alerts` | NIST 800-171 rev2 | SI-3-14-1 | Medium | Verify no unresolved Dependabot alerts |
| 1009 | `github_no_code_scanning_alerts` | NIST 800-171 rev2 | SI-3-14-1 | Medium | Verify no unresolved code scanning alerts |
| 1010 | `github_external_collaborators_limited` | NIST 800-171 rev2 | AC-3-1-6 | Medium | Verify external collaborators ≤ 5 |
| 1013 | `github_admin_members_limited` | NIST 800-53 | AC-6 | High | Verify admin members ≤ 3 |
| 1014 | `github_has_security_features` | NIST 800-53 | AC-3 | High | Verify ≥ 2 security features enabled |
| 1024 | `github_security_advisories_monitored` | NIST 800-53 | AU-2 | Medium | Verify security advisories tracked |

### Access Control & Account Management

| Check ID | Check Name | Framework | Control | Severity | Description |
|----------|------------|-----------|---------|----------|-------------|
| 1011 | `github_repository_not_archived` | NIST 800-171 rev2 | AC-3-1-1 | Low | Verify repository not archived |
| 1012 | `github_repository_not_disabled` | NIST 800-171 rev2 | AC-3-1-1 | Medium | Verify repository not disabled |
| 1018 | `github_contributors_managed` | NIST 800-53 | AC-2 | Low | Verify ≥ 1 contributors |
| 1021 | `github_collaborators_monitored` | NIST 800-53 | AU-6 | Medium | Verify collaborators ≤ 20 |
| 1028 | `github_organization_members_controlled` | NIST 800-53 | AC-2 | Medium | Verify ≥ 1 organization members |
| 1029 | `github_teams_structured` | NIST 800-53 | AC-3 | Low | Verify teams used for access control |

### Configuration & Change Management

| Check ID | Check Name | Framework | Control | Severity | Description |
|----------|------------|-----------|---------|----------|-------------|
| 1003 | `github_minimum_branch_count` | NIST 800-53 | CM-8 | Low | Verify ≥ 3 branches |
| 1017 | `github_recent_activity` | NIST 800-53 | CM-8 | Low | Verify ≥ 10 total commits |
| 1020 | `github_template_usage_controlled` | NIST 800-53 | CM-6 | Low | Verify repository not template |
| 1023 | `github_pull_requests_active` | NIST 800-53 | CM-3 | Low | Verify ≥ 5 pull requests |

### System Monitoring & Maintenance

| Check ID | Check Name | Framework | Control | Severity | Description |
|----------|------------|-----------|---------|----------|-------------|
| 1015 | `github_webhooks_secured` | NIST 800-53 | MA-4 | Medium | Verify webhooks ≤ 5 |
| 1016 | `github_active_webhooks_monitored` | NIST 800-53 | SI-4 | Medium | Verify active webhooks ≤ 3 |

### Incident Response & Issue Management

| Check ID | Check Name | Framework | Control | Severity | Description |
|----------|------------|-----------|---------|----------|-------------|
| 1019 | `github_issues_enabled` | NIST 800-53 | IR-4 | Low | Verify issues enabled |
| 1022 | `github_open_issues_managed` | NIST 800-53 | IR-4 | Low | Verify open issues ≤ 50 |

### CI/CD & Workflow Management

| Check ID | Check Name | Framework | Control | Severity | Description |
|----------|------------|-----------|---------|----------|-------------|
| 1025 | `github_workflows_controlled` | NIST 800-171 rev2 | AC-3-1-2 | Medium | Verify workflows ≤ 10 |
| 1026 | `github_active_workflows_monitored` | NIST 800-53 | SA-9 | Medium | Verify active workflows ≤ 5 |
| 1027 | `github_recent_workflow_activity` | NIST 800-53 | SA-11 | Low | Verify ≥ 3 recent workflow runs |

### Governance & Compliance

| Check ID | Check Name | Framework | Control | Severity | Description |
|----------|------------|-----------|---------|----------|-------------|
| 1030 | `github_repository_has_license` | NIST 800-53 | PM-1 | Low | Verify repository has license |

## AWS Checks (Connection ID: 2)

### EC2 Security

| Check ID | Check Name | Framework | Control | Resource Type | Severity | Description |
|----------|------------|-----------|---------|---------------|----------|-------------|
| 2001 | `aws_ec2_security_groups_no_open_ingress` | NIST 800-53 | AC-3 | AWSEC2Resource | High | Verify no security groups allow 0.0.0.0/0 ingress |

### Identity & Access Management

| Check ID | Check Name | Framework | Control | Resource Type | Severity | Description |
|----------|------------|-----------|---------|---------------|----------|-------------|
| 2002 | `aws_iam_users_have_mfa` | NIST 800-53 | IA-2 | AWSIAMResource | High | Verify all IAM users have MFA enabled |

### Storage Security

| Check ID | Check Name | Framework | Control | Resource Type | Severity | Description |
|----------|------------|-----------|---------|---------------|----------|-------------|
| 2003 | `aws_s3_buckets_encrypted` | NIST 800-53 | SC-8 | AWSS3Resource | High | Verify all S3 buckets have encryption enabled |

### Audit & Logging

| Check ID | Check Name | Framework | Control | Resource Type | Severity | Description |
|----------|------------|-----------|---------|---------------|----------|-------------|
| 2004 | `aws_cloudtrail_logging_enabled` | NIST 800-53 | AU-2 | AWSCloudTrailResource | High | Verify CloudTrail logging enabled |
| 2005 | `aws_cloudwatch_log_groups_exist` | NIST 800-53 | SI-4 | AWSCloudWatchResource | Medium | Verify CloudWatch log groups exist |

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
- ✅ **GithubResource**: 30 checks implemented
- ✅ **AWSEC2Resource**: 1 check implemented  
- ✅ **AWSIAMResource**: 1 check implemented
- ✅ **AWSS3Resource**: 1 check implemented
- ✅ **AWSCloudTrailResource**: 1 check implemented
- ✅ **AWSCloudWatchResource**: 1 check implemented

### Severity Distribution
- **High**: 9 checks (26%)
- **Medium**: 11 checks (31%) 
- **Low**: 15 checks (43%)

## Next Steps

### Areas for Expansion

1. **Additional AWS Services**
   - RDS (Database security)
   - VPC (Network security)  
   - Lambda (Serverless security)
   - ECS/EKS (Container security)
   - KMS (Key management)

2. **Additional GitHub Security**
   - Repository secrets management
   - Branch protection rules details
   - Dependency security policies
   - Organization security policies

3. **Additional Frameworks**
   - ISO 27001
   - SOC 2
   - CIS Controls
   - AWS Security Best Practices

4. **Enhanced Coverage**
   - Complete NIST 800-53 control family coverage
   - Complete NIST 800-171 control coverage
   - Cross-platform control mapping

## File Structure

```
con_mon/
├── checks/
│   ├── checks.yaml          # All check definitions
│   ├── models.py            # Check evaluation logic
│   └── __init__.py          # Check loading and filtering
├── resources/
│   ├── resources.yaml       # Resource schema definitions
│   ├── dynamic_models.py    # Dynamic model generation
│   └── models.py            # Base resource models
└── connectors/
    ├── connectors.yaml      # Connector configurations
    └── __init__.py          # Connector loading
```

## Usage

```bash
# Run all GitHub checks
python main_new.py --provider github --github-token $GITHUB_TOKEN

# Run all AWS checks  
python main_new.py --provider aws

# Run specific checks by ID
python main_new.py --provider github --check-ids 1001,1002,1003
```

---

*Last updated: [Current Date]*
*Total checks: 35 (30 GitHub + 5 AWS)* 