# KOVR Resource Collector - Compliance Checks

This document tracks all implemented compliance checks for cloud resource monitoring and security assessment.

## Overview

- **Frameworks**: 2 (NIST 800-53, NIST 800-171 rev2 Catalog)
- **Standards**: 15 total (14 active) including FedRAMP, CMMC 2.0, DOD SRG Impact Levels
- **Control Count**: 1,309 total controls (NIST 800-53: 1,199, NIST 800-171 rev2: 110)

# Checks for NIST 800-53 Controls
- **Total Controls**: 1,199
- **Control Groups**: 21 control families
- **Group Coverage**: 10 of 21 families covered (47.6%)
- **Control Coverage**: 83 of 1,199 controls covered (6.9%)

## NIST 800-53 Control Family Coverage

| Family | Controls Covered | Total Controls | Coverage % | Description |
|--------|------------------|----------------|------------|-------------|
| **AC** | 7 | 25 | 28.0% | Access Control |
| **MA** | 2 | 7 | 28.6% | Maintenance |
| **MP** | 2 | 8 | 25.0% | Media Protection |
| **IA** | 3 | 12 | 25.0% | Identification and Authentication |
| **CM** | 3 | 14 | 21.4% | Configuration Management |
| **CA** | 2 | 9 | 22.2% | Assessment, Authorization, and Monitoring |
| **IR** | 2 | 10 | 20.0% | Incident Response |
| **AT** | 1 | 6 | 16.7% | Awareness and Training |
| **PS** | 1 | 8 | 12.5% | Personnel Security |
| **AU** | 2 | 16 | 12.5% | Audit and Accountability |
| **RA** | 1 | 10 | 10.0% | Risk Assessment |
| **PE** | 1 | 23 | 4.3% | Physical and Environmental Protection |
| **SC** | 2 | 51 | 3.9% | System and Communications Protection |
| **SI** | 2 | 23 | 8.7% | System and Information Integrity |
| **CP** | 0 | 13 | 0.0% | Contingency Planning |
| **PL** | 0 | 11 | 0.0% | Planning |
| **PM** | 0 | 31 | 0.0% | Program Management |
| **PT** | 0 | 8 | 0.0% | Personally Identifiable Information Processing |
| **SA** | 0 | 23 | 0.0% | System and Services Acquisition |
| **SR** | 0 | 12 | 0.0% | Supply Chain Risk Management |

**Summary**: 14 of 20 families covered • 83 of 1,006 controls covered • 11 families with no coverage

# Checks for NIST 800-171 rev2 Catalog
- **Total Controls**: 110
- **Control Groups**: 14 control families
- **Group Coverage**: 14 of 14 families covered (100%)
- **Control Coverage**: 62 of 110 controls covered (56.4%)

## NIST 800-171 rev2 Control Family Coverage

| Family | Controls Covered | Total Controls | Coverage % | Description |
|--------|------------------|----------------|------------|-------------|
| **AT** | 2 | 3 | 66.7% | Awareness and Training |
| **IR** | 2 | 3 | 66.7% | Incident Response |
| **MA** | 4 | 6 | 66.7% | Maintenance |
| **PE** | 4 | 6 | 66.7% | Physical and Environmental Protection |
| **RA** | 2 | 3 | 66.7% | Risk Assessment |
| **SI** | 4 | 7 | 57.1% | System and Information Integrity |
| **SC** | 9 | 16 | 56.2% | System and Communications Protection |
| **AU** | 5 | 9 | 55.6% | Audit and Accountability |
| **CM** | 5 | 9 | 55.6% | Configuration Management |
| **MP** | 5 | 9 | 55.6% | Media Protection |
| **IA** | 6 | 11 | 54.5% | Identification and Authentication |
| **AC** | 11 | 22 | 50.0% | Access Control |
| **CA** | 2 | 4 | 50.0% | Security Assessment and Authorization |
| **PS** | 1 | 2 | 50.0% | Personnel Security |

*Note: All 14 control families now have 50%+ coverage*

## Supported Frameworks

| Framework ID | Framework Name | Controls | Check Coverage | Description |
|-------------|----------------|----------|----------------|-------------|
| 2 | NIST 800-53 | 1,006 | 148 checks | Security and Privacy Controls for Federal Information Systems |
| 3 | NIST 800-171 rev2 Catalog | 110 | 125 checks | Protecting Controlled Unclassified Information |

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

### GitHub Checks for NIST 800-171 rev2 (63 checks)

| Control Family | Checks | Key Controls | Description |
|----------------|--------|--------------|-------------|
| **Access Control (AC)** | 11 | AC-3-1-1, AC-3-1-3, AC-3-1-7, AC-3-1-8, AC-3-1-9, AC-3-1-10 | Account management, access enforcement, separation of duties, least privilege |
| **Awareness and Training (AT)** | 2 | AT-3-2-1, AT-3-2-2 | Security awareness through security features and documentation |
| **Audit and Accountability (AU)** | 5 | AU-3-3-1, AU-3-3-2, AU-3-3-3, AU-3-3-4, AU-3-3-5 | Event logging, audit record content, generation, review, reduction |
| **Configuration Management (CM)** | 5 | CM-3-4-1, CM-3-4-3, CM-3-4-4, CM-3-4-5 | Baseline configuration, change control, monitoring, documentation |
| **Identification and Authentication (IA)** | 6 | IA-3-5-1, IA-3-5-2, IA-3-5-4, IA-3-5-5 | User identification, authenticator management, feedback |
| **Incident Response (IR)** | 2 | IR-3-6-1, IR-3-6-2 | Incident response plan, monitoring |
| **Maintenance (MA)** | 4 | MA-3-7-1, MA-3-7-2, MA-3-7-3, MA-3-7-4 | Organizational maintenance, personnel, controls, tools |
| **Media Protection (MP)** | 5 | MP-3-8-1, MP-3-8-2, MP-3-8-3, MP-3-8-4, MP-3-8-5 | Media storage, access control, labeling, handling, transport |
| **Physical Protection (PE)** | 4 | PE-3-10-1, PE-3-10-2, PE-3-10-3, PE-3-10-4 | Physical access controls, facility controls, environmental monitoring |
| **Personnel Security (PS)** | 1 | PS-3-9-1 | Personnel screening |
| **Risk Assessment (RA)** | 2 | RA-3-11-1, RA-3-11-2 | Risk assessment, categorization |
| **System Communications Protection (SC)** | 9 | SC-3-13-1, SC-3-13-2, SC-3-13-3, SC-3-13-4, SC-3-13-5, SC-3-13-6, SC-3-13-7, SC-3-13-8, SC-3-13-9 | System protection, boundary protection, network segmentation, cryptographic protection |
| **System Information Integrity (SI)** | 4 | SI-3-14-1, SI-3-14-2, SI-3-14-3, SI-3-14-4 | Flaw remediation, malicious code protection, monitoring, software integrity |
| **Security Assessment (CA)** | 2 | CA-3-12-1, CA-3-12-3 | Security assessment, continuous monitoring |

### AWS Checks for NIST 800-171 rev2 (62 checks)

| Control Family | Checks | Key Controls | Description |
|----------------|--------|--------------|-------------|
| **Access Control (AC)** | 10 | AC-3-1-1, AC-3-1-3, AC-3-1-7, AC-3-1-8, AC-3-1-9, AC-3-1-10 | IAM account management, security groups, least privilege, information flow |
| **Awareness and Training (AT)** | 2 | AT-3-2-1, AT-3-2-2 | CloudTrail logging for awareness and training |
| **Audit and Accountability (AU)** | 5 | AU-3-3-1, AU-3-3-2, AU-3-3-3, AU-3-3-4, AU-3-3-5 | CloudTrail logging, CloudWatch audit records, metrics, dashboards |
| **Configuration Management (CM)** | 4 | CM-3-4-1, CM-3-4-2, CM-3-4-4, CM-3-4-5 | Baseline configuration, security group settings, EC2 monitoring |
| **Identification and Authentication (IA)** | 6 | IA-3-5-1, IA-3-5-2, IA-3-5-3, IA-3-5-4, IA-3-5-5 | User identification, multi-factor authentication, IAM management |
| **Incident Response (IR)** | 2 | IR-3-6-1, IR-3-6-2 | CloudTrail incident response, CloudWatch monitoring |
| **Maintenance (MA)** | 3 | MA-3-7-1, MA-3-7-2, MA-3-7-3 | Resource tagging, IAM relationships, EC2 snapshots |
| **Media Protection (MP)** | 5 | MP-3-8-1, MP-3-8-2, MP-3-8-3, MP-3-8-4, MP-3-8-5 | S3 encryption, bucket access control, policies, transport |
| **Physical Protection (PE)** | 3 | PE-3-10-1, PE-3-10-2, PE-3-10-3, PE-3-10-4 | Multi-AZ deployment, subnets, VPC security, CloudWatch monitoring |
| **Personnel Security (PS)** | 1 | PS-3-9-1 | IAM user groups |
| **Risk Assessment (RA)** | 2 | RA-3-11-1, RA-3-11-2 | Security group risk analysis, resource classification |
| **System Communications Protection (SC)** | 7 | SC-3-13-1, SC-3-13-2, SC-3-13-3, SC-3-13-4, SC-3-13-5, SC-3-13-6, SC-3-13-8, SC-3-13-9 | VPC configuration, security groups, network segmentation, S3 encryption |
| **System Information Integrity (SI)** | 4 | SI-3-14-1, SI-3-14-2, SI-3-14-3, SI-3-14-4 | Instance patching, security group protection, CloudWatch monitoring |
| **Security Assessment (CA)** | 2 | CA-3-12-1, CA-3-12-3 | CloudTrail assessment, CloudWatch monitoring |

## Removed Checks

The following NIST 800-171 rev2 checks were removed due to missing field data:

| ID | Control | Field Path | Issue | Status |
|----|---------|------------|-------|---------|
| 10102 | AC-3-1-2 | `collaboration_data.collaborators_by_permission` | Field does not exist in schema | Removed |
| 10402 | AT-3-2-2 | `collaboration_data.collaborators_by_permission` | Field does not exist in schema | Removed |
| 10801 | MP-3-8-1 | `organization_data.two_factor_requirement_enabled` | Field does not exist in schema | Removed |
| 10901 | PE-3-10-1 | `organization_data.two_factor_requirement_enabled` | Field does not exist in schema | Removed |

