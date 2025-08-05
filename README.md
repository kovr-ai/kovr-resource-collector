## KOVR Resource Collector

A comprehensive compliance monitoring system that collects and validates cloud resources against various security frameworks including NIST 800-53 rev5 and NIST 800-171 rev2.

## Overview

This system provides automated compliance checks for GitHub repositories and AWS cloud resources, enabling organizations to monitor their security posture against established frameworks.

### Key Features

- **Multi-Platform Support**: GitHub repositories and AWS cloud resources
- **Framework Compliance**: NIST 800-53 rev5 and NIST 800-171 rev2 frameworks
- **Automated Validation**: Configurable checks with various comparison operations
- **Comprehensive Coverage**: 273 total compliance checks across multiple control families
- **Flexible Architecture**: YAML-based configuration with custom logic support

## Supported Frameworks

| Framework | Total Controls | Covered Controls | Coverage | Total Checks |
|-----------|----------------|------------------|----------|--------------|
| NIST 800-53 rev5 | 1,006 | 83 | 8.3% | 148 |
| **NIST 800-171 rev2** | **110** | **62** | **56.4%** | **125** |

## Framework Coverage Analysis

### NIST 800-171 rev2 Control Family Coverage

All control families now have **50%+ coverage** as of the latest update:

| Family | Description | Total Controls | Covered | Coverage | Status |
|--------|-------------|----------------|---------|----------|---------|
| **AC** | Access Control | 22 | 11 | **50.0%** | ✅ Target Met |
| **AT** | Awareness and Training | 3 | 2 | **66.7%** | ✅ Above Target |
| **AU** | Audit and Accountability | 9 | 5 | **55.6%** | ✅ Above Target |
| **CA** | Security Assessment | 4 | 2 | **50.0%** | ✅ Target Met |
| **CM** | Configuration Management | 9 | 5 | **55.6%** | ✅ Above Target |
| **IA** | Identification and Authentication | 11 | 6 | **54.5%** | ✅ Above Target |
| **IR** | Incident Response | 3 | 2 | **66.7%** | ✅ Above Target |
| **MA** | Maintenance | 6 | 4 | **66.7%** | ✅ Above Target |
| **MP** | Media Protection | 9 | 5 | **55.6%** | ✅ Above Target |
| **PE** | Physical and Environmental Protection | 6 | 4 | **66.7%** | ✅ Above Target |
| **PS** | Personnel Security | 2 | 1 | **50.0%** | ✅ Target Met |
| **RA** | Risk Assessment | 3 | 2 | **66.7%** | ✅ Above Target |
| **SC** | System and Communications Protection | 16 | 9 | **56.2%** | ✅ Above Target |
| **SI** | System and Information Integrity | 7 | 4 | **57.1%** | ✅ Above Target |

### NIST 800-53 Control Family Coverage

| Family | Description | Total Controls | Covered | Coverage |
|--------|-------------|----------------|---------|----------|
| AC | Access Control | 25 | 7 | 28.0% |
| AT | Awareness and Training | 6 | 1 | 16.7% |
| AU | Audit and Accountability | 16 | 2 | 12.5% |
| CA | Security Assessment | 9 | 2 | 22.2% |
| CM | Configuration Management | 14 | 3 | 21.4% |
| CP | Contingency Planning | 13 | 0 | 0.0% |
| IA | Identification and Authentication | 12 | 3 | 25.0% |
| IR | Incident Response | 10 | 2 | 20.0% |
| MA | Maintenance | 7 | 2 | 28.6% |
| MP | Media Protection | 8 | 2 | 25.0% |
| PE | Physical and Environmental Protection | 23 | 1 | 4.3% |
| PL | Planning | 11 | 0 | 0.0% |
| PM | Program Management | 31 | 0 | 0.0% |
| PS | Personnel Security | 8 | 1 | 12.5% |
| PT | Personally Identifiable Information Processing | 8 | 0 | 0.0% |
| RA | Risk Assessment | 10 | 1 | 10.0% |
| SA | System and Services Acquisition | 23 | 0 | 0.0% |
| SC | System and Communications Protection | 51 | 2 | 3.9% |
| SI | System and Information Integrity | 23 | 2 | 8.7% |
| SR | Supply Chain Risk Management | 12 | 0 | 0.0% |
| **Total** | **All Families** | **1,006** | **83** | **8.3%** |

**Note**: 11 NIST 800-53 control families (CP, PL, PM, PT, SA, SR) currently have no coverage (0.0%).

### Most Implemented NIST 800-53 Controls

| Control Family | Total Checks | Coverage Percentage |
|----------------|--------------|-------------------|
| Access Control (AC) | 35 | 28.0% |
| Maintenance (MA) | 14 | 28.6% |
| Media Protection (MP) | 12 | 25.0% |
| Identification and Authentication (IA) | 12 | 25.0% |
| Security Assessment (CA) | 11 | 22.2% |

## Recent Updates

### Version 2.1 - Enhanced NIST 800-171 rev2 Coverage
- **Achievement**: All 14 control families now have 50%+ coverage
- **Added**: 64 new compliance checks (IDs 21304-21366)
- **Coverage Improvement**: Increased from 40.0% to 56.4% overall coverage
- **Family Improvements**:
  - AC (Access Control): 27.3% → 50.0%
  - AT (Awareness Training): 33.3% → 66.7%
  - AU (Audit & Accountability): 22.2% → 55.6%
  - CM (Configuration Management): 33.3% → 55.6%
  - IA (Identification & Authentication): 27.3% → 54.5%
  - MA (Maintenance): 33.3% → 66.7%
  - MP (Media Protection): 22.2% → 55.6%
  - PE (Physical & Environmental Protection): 16.7% → 66.7%
  - RA (Risk Assessment): 33.3% → 66.7%
  - SC (System & Communications Protection): 12.5% → 56.2%
  - SI (System & Information Integrity): 28.6% → 57.1%

## Check Structure

Each compliance check includes:
- **ID**: Unique identifier
- **Connection**: Platform (1=GitHub, 2=AWS)
- **Framework**: NIST 800-53 rev5 (ID=1) or NIST 800-171 rev2 (ID=3)
- **Control Mapping**: Links to specific framework controls
- **Resource Type**: Target resource (GithubResource, AWSIAMResource, etc.)
- **Validation Logic**: Field paths, operations, and expected values
- **Metadata**: Tags, severity levels, and categories

### Example Check

```yaml
- id: 21303
  connection_id: 1
  name: "github_access_control_ac_3_1_3"
  description: "Verify access control through repository permissions"
  framework_id: 3
  framework_name: "NIST 800-171 rev2 Catalog"
  control_id: 1202
  control_name: "AC-3-1-3"
  resource_type: "GithubResource"
  field_path: "collaboration_data.total_collaborators"
  operation:
    name: "GREATER_THAN"
  expected_value: 0
  tags: ["security", "github", "access_control", "permissions"]
  severity: "medium"
  category: "access_control"
```

## Removed Checks

The following NIST 800-171 rev2 checks were removed due to missing field data:

| ID | Control | Field Path | Issue | Status |
|----|---------|------------|-------|---------|
| 10102 | AC-3-1-2 | `collaboration_data.collaborators_by_permission` | Field does not exist in schema | Removed |
| 10402 | AT-3-2-2 | `collaboration_data.collaborators_by_permission` | Field does not exist in schema | Removed |
| 10801 | MP-3-8-1 | `organization_data.two_factor_requirement_enabled` | Field does not exist in schema | Removed |
| 10901 | PE-3-10-1 | `organization_data.two_factor_requirement_enabled` | Field does not exist in schema | Removed |

## Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure your connections and checks
4. Run compliance validation

## Usage

```bash
# Run all checks
python main_new.py

# Run specific connection
CONNECTION_ID=1 python main_new.py

# Run specific checks
CHECK_IDS="10001,10002" python main_new.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add new checks following the established patterns
4. Test your changes
5. Submit a pull request

## License

[Add your license information here]

