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
- **Control Coverage**: 18 of 1,199 controls covered (1.5%)

## NIST 800-53 Control Family Coverage

| Family | Controls Covered | Total Controls | Coverage % | Description |
|--------|------------------|----------------|------------|-------------|
| **CM** | 4 | 66 | 6.1% | Configuration Management |
| **AT** | 1 | 17 | 5.9% | Awareness and Training |
| **PS** | 1 | 18 | 5.6% | Personnel Security |
| **PT** | 1 | 21 | 4.8% | Privacy Controls |
| **AC** | 5 | 147 | 3.4% | Access Control |
| **MP** | 1 | 30 | 3.3% | Media Protection |
| **PM** | 1 | 37 | 2.7% | Program Management |
| **IR** | 1 | 42 | 2.4% | Incident Response |
| **PE** | 1 | 59 | 1.7% | Physical and Environmental Protection |
| **SA** | 2 | 145 | 1.4% | System and Services Acquisition |
| **SC** | 0 | 162 | 0.0% | System and Communications Protection |
| **SI** | 0 | 118 | 0.0% | System and Information Integrity |
| **IA** | 0 | 70 | 0.0% | Identification and Authentication |
| **AU** | 0 | 69 | 0.0% | Audit and Accountability |
| **CP** | 0 | 56 | 0.0% | Contingency Planning |
| **CA** | 0 | 32 | 0.0% | Assessment, Authorization, and Monitoring |
| **MA** | 0 | 30 | 0.0% | Maintenance |
| **SR** | 0 | 27 | 0.0% | Supply Chain Risk Management |
| **RA** | 0 | 26 | 0.0% | Risk Assessment |
| **PL** | 0 | 17 | 0.0% | Planning |
| **GRR** | 0 | 10 | 0.0% | DoD PKI Authentication |

**Summary**: 10 of 21 families covered • 18 of 1,199 controls covered • 637 controls in uncovered families

# Checks for NIST 800-171 rev2 Catalog
- **Total Controls**: 110
- **Control Groups**: 14 control families
- **Group Coverage**: 14 of 14 families covered (100%)
- **Control Coverage**: 62 of 110 controls covered (56.4%)

## NIST 800-171 rev2 Control Family Coverage

| Family | Controls Covered | Total Controls | Coverage % | Description |
|--------|------------------|----------------|------------|-------------|
| **IR** | 2 | 3 | 66.7% | Incident Response |
| **AT** | 2 | 3 | 66.7% | Awareness and Training |
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
| 2 | NIST 800-53 | 1,199 | 148 checks | Security and Privacy Controls for Federal Information Systems |
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

### AWS Checks for NIST 800-171 rev2 (62 checks)

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
