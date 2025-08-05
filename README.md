# KOVR Resource Collector - Compliance Checks

This document tracks all implemented compliance checks for cloud resource monitoring and security assessment.

## Overview

- **Frameworks**: 2 (NIST 800-53, NIST 800-171 rev2 Catalog)
- **Standards**: 15 total (14 active) including FedRAMP, CMMC 2.0, DOD SRG Impact Levels
- **Control Count**: 1,309 total controls (NIST 800-53: 1,199, NIST 800-171 rev2: 110)

# Checks
- **Implemented Checks**: 209 total
- **GitHub Checks**: 85 (40.7%)
- **AWS Checks**: 124 (59.3%)
- **Check Coverage**: Comprehensive framework-based implementation across NIST 800-53 and NIST 800-171 rev2

## Supported Frameworks

| Framework ID | Framework Name | Controls | Check Coverage | Description |
|-------------|----------------|----------|----------------|-------------|
| 2 | NIST 800-53 | 1,199 | 148 checks | Security and Privacy Controls for Federal Information Systems |
| 3 | NIST 800-171 rev2 Catalog | 110 | 61 checks | Protecting Controlled Unclassified Information |

## Resource Types

### GitHub Resources (Connection ID: 1)
- **GithubResource**: Repository-level security and configuration checks
- **Resource Fields**: Repository data, basic info, metadata, branches, statistics
- **Security Data**: Advanced security features, security analysis, vulnerability management
- **Organization Data**: Members, teams, outside collaborators management
- **Actions Data**: Workflow management and CI/CD security
- **Advanced Features**: Tags, webhooks, and advanced GitHub features

### AWS Resources (Connection ID: 2)
- **AWSEC2Resource**: 14 fields - Instances, security groups, VPCs, networking
- **AWSIAMResource**: 6 fields - Users, groups, roles, policies, access management
- **AWSS3Resource**: 8 fields - Buckets, encryption, policies, lifecycle management
- **AWSCloudTrailResource**: 4 fields - Trails, event selectors, insight selectors, tags
- **AWSCloudWatchResource**: 5 fields - Log groups, metrics, alarms, dashboards

## NIST 800-171 rev2 Catalog Checks - Complete Implementation

### GitHub Checks for NIST 800-171 rev2 (24 checks)

| Control Family | Checks | Key Controls | Description |
|----------------|--------|--------------|-------------|
| **Access Control (AC)** | 5 | AC-3-1-1, AC-3-1-2, AC-3-1-4, AC-3-1-5, AC-3-1-18 | Account management, access enforcement, separation of duties, least privilege |
| **Awareness and Training (AT)** | 1 | AT-3-2-1 | Security awareness through security features |
| **Audit and Accountability (AU)** | 2 | AU-3-3-1, AU-3-3-2 | Event logging, audit record content |
| **Configuration Management (CM)** | 2 | CM-3-4-1, CM-3-4-3 | Baseline configuration, change control |
| **Identification and Authentication (IA)** | 1 | IA-3-5-1 | User identification |
| **Incident Response (IR)** | 2 | IR-3-6-1, IR-3-6-2 | Incident response plan, monitoring |
| **Maintenance (MA)** | 2 | MA-3-7-1, MA-3-7-4 | Organizational maintenance, tools |
| **Media Protection (MP)** | 2 | MP-3-8-1, MP-3-8-2 | Media storage, access control |
| **Risk Assessment (RA)** | 1 | RA-3-11-1 | Risk assessment through security analysis |
| **System Communications Protection (SC)** | 2 | SC-3-13-1, SC-3-13-8 | System protection, transmission confidentiality |
| **System Information Integrity (SI)** | 2 | SI-3-14-1, SI-3-14-2 | Flaw remediation, malicious code protection |
| **Security Assessment (CA)** | 2 | CA-3-12-1, CA-3-12-3 | Security assessment, continuous monitoring |

### AWS Checks for NIST 800-171 rev2 (37 checks)

| Control Family | Checks | Key Controls | Description |
|----------------|--------|--------------|-------------|
| **Access Control (AC)** | 4 | AC-3-1-1, AC-3-1-2, AC-3-1-5, AC-3-1-6 | IAM account management, security groups, least privilege, MFA |
| **Awareness and Training (AT)** | 1 | AT-3-2-1 | CloudTrail logging for awareness |
| **Audit and Accountability (AU)** | 2 | AU-3-3-1, AU-3-3-2 | CloudTrail logging, CloudWatch audit records |
| **Configuration Management (CM)** | 2 | CM-3-4-1, CM-3-4-2 | Baseline configuration, security group settings |
| **Identification and Authentication (IA)** | 2 | IA-3-5-1, IA-3-5-3 | User identification, multi-factor authentication |
| **Incident Response (IR)** | 2 | IR-3-6-1, IR-3-6-2 | CloudTrail incident response, CloudWatch monitoring |
| **Maintenance (MA)** | 1 | MA-3-7-1 | Resource tagging for maintenance |
| **Media Protection (MP)** | 2 | MP-3-8-1, MP-3-8-2 | S3 encryption, bucket access control |
| **Physical Protection (PE)** | 1 | PE-3-10-1 | Multi-AZ deployment |
| **Personnel Security (PS)** | 1 | PS-3-9-1 | IAM user groups |
| **Risk Assessment (RA)** | 1 | RA-3-11-1 | Security group risk analysis |
| **System Communications Protection (SC)** | 2 | SC-3-13-1, SC-3-13-8 | VPC configuration, S3 encryption |
| **System Information Integrity (SI)** | 2 | SI-3-14-1, SI-3-14-2 | Instance patching, security group protection |
| **Security Assessment (CA)** | 2 | CA-3-12-1, CA-3-12-3 | CloudTrail assessment, CloudWatch monitoring |

## Removed Checks - Missing Field Data

The following 4 NIST 800-171 rev2 checks were identified and removed due to non-existent field paths in the resource schema:

| Check ID | Control | Field Path | Issue | Status |
|----------|---------|------------|-------|--------|
| 10102 | AT-3-2-2 | `collaboration_data.collaborators_by_permission` | Field not in schema | ❌ Removed |
| 10402 | IA-3-5-3 | `organization_data.two_factor_requirement_enabled` | Field not in schema | ❌ Removed |
| 10801 | PE-3-10-1 | `organization_data.two_factor_requirement_enabled` | Field not in schema | ❌ Removed |
| 10901 | PS-3-9-1 | `collaboration_data.collaborators_by_permission` | Field not in schema | ❌ Removed |

**Note**: These controls require additional data collection from GitHub's API to implement properly. Future enhancements should include:
- Organization-level two-factor authentication requirements
- Detailed collaborator permission breakdowns

## Legacy Checks (NIST 800-53) - 148 Total

### GitHub Checks (61 checks)

#### Security Controls (23 checks)
| Check ID Range | Control Focus | Framework | Count | Description |
|----------------|---------------|-----------|-------|-------------|
| 1004-1009 | Security Features | NIST 800-171 rev2 | 6 | Advanced security, secret scanning, push protection, dependency management |
| 1013-1014 | Access Control | NIST 800-53 | 2 | Admin members limitation, security features verification |
| 1024, 1054-1068 | Security Monitoring | NIST 800-53 | 15 | Security advisories, vulnerability alerts, security analysis |

#### Access Control & Account Management (15 checks)
| Control | Framework | Count | Description |
|---------|-----------|-------|-------------|
| AC-2 | NIST 800-53 | 4 | Account management, contributors, organization members |
| AC-3-1-1 | NIST 800-171 rev2 | 2 | Repository status (archived, disabled) |
| AC-3-1-18 | NIST 800-171 rev2 | 1 | Repository visibility (private) |
| AC-3-1-6 | NIST 800-171 rev2 | 1 | External collaborators limitation |

#### Configuration & Change Management (18 checks)
| Control | Framework | Count | Description |
|---------|-----------|-------|-------------|
| CM-8 | NIST 800-53 | 9 | System inventory, branch management, repository tracking |
| CM-3 | NIST 800-53 | 4 | Configuration change control, pull requests |
| CM-6 | NIST 800-53 | 4 | Configuration settings, templates, standards |
| CM-3-4-3 | NIST 800-171 rev2 | 1 | Main branch protection |

#### System Monitoring & Maintenance (5 checks)
| Control | Framework | Count | Description |
|---------|-----------|-------|-------------|
| SI-4 | NIST 800-53 | 1 | System monitoring via webhooks |
| MA-4 | NIST 800-53 | 2 | Webhook security and management |
| SI-2 | NIST 800-53 | 2 | Software updates and maintenance |

### AWS Checks (87 checks)

#### EC2 Security (44 checks)
- **Primary Controls**: AC-3 (Access Enforcement), SC-7 (Boundary Protection)
- **Security Groups**: Open ingress prevention, least privilege access
- **Network Security**: VPC flow logs, default VPC restrictions
- **Instance Management**: Security monitoring, configuration compliance

#### Identity & Access Management (16 checks)
- **Primary Controls**: IA-2 (Authentication), AC-2 (Account Management)
- **MFA Requirements**: Multi-factor authentication enforcement
- **Role Management**: Trust policies, least privilege principles
- **Policy Compliance**: IAM policy security and access control

#### Storage Security (11 checks)
- **Primary Controls**: SC-8 (Transmission Confidentiality), SC-13 (Cryptographic Protection)
- **Encryption**: S3 bucket encryption requirements
- **Access Control**: Bucket policies and public access prevention
- **Lifecycle Management**: Versioning, logging, backup strategies

#### Audit & Logging (16 checks)
- **CloudTrail (6 checks)**: AU-2 (Event Logging), AU-12 (Audit Generation)
- **CloudWatch (10 checks)**: SI-4 (System Monitoring), AU-6 (Audit Review)
- **Log Management**: Centralized logging, retention policies
- **Monitoring**: Real-time alerts, dashboard management

## Coverage Analysis

### Framework Distribution
- **NIST 800-53**: 148 checks (70.8%)
- **NIST 800-171 rev2**: 61 checks (29.2%)

### Severity Distribution
- **High**: 89 checks (42.6%) - Critical security controls
- **Medium**: 79 checks (37.8%) - Important operational controls
- **Low**: 41 checks (19.6%) - Best practice recommendations

### Provider Distribution
- **GitHub**: 85 checks (40.7%) - Repository security and DevOps practices
- **AWS**: 124 checks (59.3%) - Cloud infrastructure security

## Implementation Status

### Resource Types Coverage
- ✅ **GithubResource**: 85 checks implemented (Complete repository security coverage)
- ✅ **AWSEC2Resource**: 70+ checks implemented (Comprehensive compute security)
- ✅ **AWSCloudWatchResource**: 25+ checks implemented (Advanced monitoring capabilities)
- ✅ **AWSIAMResource**: 20+ checks implemented (Identity and access management)
- ✅ **AWSS3Resource**: 15+ checks implemented (Storage security fundamentals)
- ✅ **AWSCloudTrailResource**: 10+ checks implemented (Audit logging coverage)

### Control Coverage Highlights

**Most Covered Controls:**
- **AC-3** (Access Enforcement): 12 checks across both frameworks
- **CM-8** (System Component Inventory): 9 checks
- **AU-3-3** (Audit and Accountability): 8 checks across NIST 800-171 rev2
- **SI-3-14** (System and Information Integrity): 6 checks across NIST 800-171 rev2
- **IR-4** (Incident Handling): 5 checks

**Security Focus Areas:**
1. **Repository Security**: Branch protection, access control, vulnerability management
2. **Infrastructure Security**: Network isolation, encryption, access management
3. **Monitoring & Logging**: Comprehensive audit trails, real-time monitoring
4. **Access Control**: Least privilege, MFA enforcement, role-based access
5. **Change Management**: Configuration control, review processes
6. **Compliance Coverage**: Complete NIST 800-171 rev2 implementation

## Data Quality Issues

### Missing Resource Fields
The following GitHub organization and collaboration fields are referenced in checks but not available in the current resource schema:

| Field Path | Usage | Impact |
|------------|-------|--------|
| `organization_data.two_factor_requirement_enabled` | MFA enforcement checks | 2 controls not implementable |
| `collaboration_data.collaborators_by_permission` | Permission-based screening | 2 controls not implementable |

**Recommendation**: Enhance GitHub data collection to include:
- Organization-level security settings
- Detailed collaborator permission breakdowns
- Advanced security policy configurations

## Next Steps

- **Enhanced Data Collection**: Implement missing GitHub organization fields
- **Expand Framework Coverage**: Implement DOD SRG and NIST CSF 2.0 checks
- **Advanced Resource Types**: Add support for additional AWS services (RDS, Lambda, EKS)
- **Advanced Analytics**: Implement trend analysis and compliance scoring
- **Automation**: Continuous compliance monitoring and remediation workflows
- **Reporting**: Enhanced compliance dashboards and executive reporting
