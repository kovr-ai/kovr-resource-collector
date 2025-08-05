"""
Data loader for cybersecurity frameworks - loads data from CSV and creates framework models.
"""

import csv
import os
from typing import List, Dict, Tuple
from datetime import datetime
from .models import Framework, Control, Standard, StandardControlMapping, FrameworkWithControls


def load_frameworks_from_csv(csv_file_path: str = None) -> Tuple[List[Framework], List[Control]]:
    """
    Load frameworks and controls from NIST CSV file.
    
    Args:
        csv_file_path: Path to CSV file, defaults to con_mon/nist.csv
        
    Returns:
        Tuple of (frameworks_list, controls_list)
    """
    if csv_file_path is None:
        # Default to nist.csv in con_mon directory
        current_dir = os.path.dirname(os.path.dirname(__file__))  # Go up to con_mon/
        csv_file_path = os.path.join(current_dir, 'nist.csv')
    
    frameworks = {}  # Use dict to avoid duplicates
    controls = []
    
    print(f"📁 Loading framework data from: {csv_file_path}")
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 since CSV has header
                try:
                    framework_name = row['Framework'].strip()
                    control_name = row['Control Name'].strip()
                    control_description = row['Control Description'].strip()
                    github_check_required = row['GitHub Check Required'].strip()
                    
                    # Parse framework information
                    framework_version = None
                    issuing_org = "NIST"  # Default since this is NIST data
                    
                    # Extract version from framework name if present
                    if "Rev " in framework_name:
                        parts = framework_name.split(" Rev ")
                        framework_base = parts[0]
                        framework_version = f"Rev {parts[1]}"
                    else:
                        framework_base = framework_name
                    
                    # Create framework if not exists
                    if framework_name not in frameworks:
                        framework_id = len(frameworks) + 1
                        frameworks[framework_name] = Framework(
                            id=framework_id,
                            name=framework_name,
                            version=framework_version,
                            description=f"Framework for {framework_base} cybersecurity controls",
                            issuing_organization=issuing_org,
                            status="active"
                        )
                    
                    # Determine control family based on control ID
                    control_family = _determine_control_family(control_name)
                    
                    # Create control
                    control = Control(
                        id=len(controls) + 1,
                        framework_id=frameworks[framework_name].id,
                        control_id=control_name,
                        name=_extract_control_title(control_name, control_description),
                        description=control_description,
                        control_family=control_family,
                        priority=_determine_priority(control_name),
                        implementation_guidance=f"GitHub Implementation: {github_check_required}",
                        github_check_required=github_check_required
                    )
                    
                    controls.append(control)
                    
                except KeyError as e:
                    print(f"⚠️  Row {row_num}: Missing required column {e}")
                    continue
                except Exception as e:
                    print(f"⚠️  Row {row_num}: Error processing row - {e}")
                    continue
        
        frameworks_list = list(frameworks.values())
        
        print(f"✅ Successfully loaded:")
        print(f"   • {len(frameworks_list)} frameworks")
        print(f"   • {len(controls)} controls")
        
        return frameworks_list, controls
        
    except FileNotFoundError:
        print(f"❌ CSV file not found: {csv_file_path}")
        raise
    except Exception as e:
        print(f"❌ Error loading CSV file: {e}")
        raise


def _determine_control_family(control_id: str) -> str:
    """Determine control family based on control ID."""
    control_id_upper = control_id.upper()
    
    # NIST 800-53 control families
    if control_id_upper.startswith('AC'):
        return 'Access Control'
    elif control_id_upper.startswith('AU'):
        return 'Audit and Accountability'
    elif control_id_upper.startswith('CM'):
        return 'Configuration Management'
    elif control_id_upper.startswith('IA'):
        return 'Identification and Authentication'
    elif control_id_upper.startswith('IR'):
        return 'Incident Response'
    elif control_id_upper.startswith('MA'):
        return 'Maintenance'
    elif control_id_upper.startswith('PM'):
        return 'Program Management'
    elif control_id_upper.startswith('SC'):
        return 'System and Communications Protection'
    elif control_id_upper.startswith('SI'):
        return 'System and Information Integrity'
    elif control_id_upper.startswith('SA'):
        return 'System and Services Acquisition'
    elif control_id_upper.startswith('CP'):
        return 'Contingency Planning'
    # NIST 800-171 control families (numerical)
    elif '3.1.' in control_id:
        return 'Access Control'
    elif '3.3.' in control_id:
        return 'Audit and Accountability'
    elif '3.4.' in control_id:
        return 'Configuration Management'
    elif '3.5.' in control_id:
        return 'Identification and Authentication'
    elif '3.13.' in control_id:
        return 'System and Communications Protection'
    elif '3.14.' in control_id:
        return 'System and Information Integrity'
    else:
        return 'Other'


def _extract_control_title(control_id: str, description: str) -> str:
    """Extract a concise title from control ID and description."""
    # Use first part of description as title, limit to reasonable length
    title_parts = description.split('.')
    title = title_parts[0].strip()
    
    # Limit title length for readability
    if len(title) > 80:
        title = title[:77] + "..."
    
    return title


def _determine_priority(control_id: str) -> str:
    """Determine control priority based on control ID and common criticality."""
    control_id_upper = control_id.upper()
    
    # High priority controls (security-critical)
    high_priority = [
        'AC-2', 'AC-3', 'AC-6',  # Access control fundamentals
        'AU-2', 'AU-6',          # Audit fundamentals
        'IA-2', 'IA-5',          # Authentication fundamentals
        'SC-8', 'SC-12',         # Crypto and transmission security
        'SI-2', 'SI-4',          # System integrity and monitoring
        '3.1.1', '3.1.2', '3.1.6',  # 800-171 access control
        '3.5.3', '3.5.9',           # 800-171 authentication
        '3.14.1'                     # 800-171 system integrity
    ]
    
    # Medium priority controls (important but not critical)
    medium_priority = [
        'CM-3', 'CM-6', 'CM-8',  # Configuration management
        'IR-4', 'MA-4',          # Incident response, maintenance
        'SA-9', 'SA-11',         # Acquisition controls
        '3.3.1', '3.3.2',        # 800-171 audit
        '3.4.6', '3.13.8'        # 800-171 config mgmt and boundary protection
    ]
    
    if any(control_id_upper.startswith(hc) or hc in control_id_upper for hc in high_priority):
        return 'high'
    elif any(control_id_upper.startswith(mc) or mc in control_id_upper for mc in medium_priority):
        return 'medium'
    else:
        return 'low'


def populate_framework_data() -> Tuple[List[FrameworkWithControls], List[Standard], List[StandardControlMapping]]:
    """
    Load and organize all framework data with relationships.
    
    Returns:
        Tuple of (frameworks_with_controls, standards, mappings)
    """
    print("🏗️  **Populating Framework Data**")
    print("=" * 50)
    
    # Load base data from CSV
    frameworks, controls = load_frameworks_from_csv()
    
    # Organize controls by framework
    frameworks_with_controls = []
    for framework in frameworks:
        framework_controls = [c for c in controls if c.framework_id == framework.id]
        
        framework_with_controls = FrameworkWithControls(
            **framework.dict(),
            controls=framework_controls
        )
        frameworks_with_controls.append(framework_with_controls)
    
    # Create sample standards (these would typically come from another data source)
    standards = [
        Standard(
            id=1,
            name="SOC 2 Type II",
            version="2017",
            description="Service Organization Control 2 for service organizations",
            issuing_organization="AICPA",
            scope="Security, Availability, Processing Integrity, Confidentiality, Privacy"
        ),
        Standard(
            id=2,
            name="ISO 27001",
            version="2013",
            description="Information Security Management Systems Requirements",
            issuing_organization="ISO/IEC",
            scope="Information Security Management"
        ),
        Standard(
            id=3,
            name="FedRAMP",
            version="Current",
            description="Federal Risk and Authorization Management Program",
            issuing_organization="GSA",
            scope="Cloud Security for Federal Agencies"
        )
    ]
    
    # Create sample standard-control mappings
    # Map some key controls to standards (in practice, this would be comprehensive)
    mappings = []
    mapping_id = 1
    
    # Map some NIST controls to SOC 2
    soc2_control_mappings = [
        ('AC-2', 'User access management'),
        ('AC-6', 'Least privilege access'),
        ('AU-2', 'Audit logging and monitoring'),
        ('IA-2', 'Multi-factor authentication'),
        ('SI-4', 'System monitoring')
    ]
    
    for control in controls:
        for mapped_control, notes in soc2_control_mappings:
            if mapped_control in control.control_id:
                mappings.append(StandardControlMapping(
                    id=mapping_id,
                    standard_id=1,  # SOC 2
                    control_id=control.id,
                    mapping_type="direct",
                    compliance_level="mandatory",
                    notes=f"SOC 2: {notes}"
                ))
                mapping_id += 1
    
    print(f"✅ Populated framework data:")
    print(f"   • {len(frameworks_with_controls)} frameworks with controls")
    print(f"   • {len(standards)} standards")
    print(f"   • {len(mappings)} standard-control mappings")
    
    return frameworks_with_controls, standards, mappings 