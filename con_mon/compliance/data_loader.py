"""
Data loader for cybersecurity frameworks - loads data from database and CSV files.
"""

import csv
import os
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from con_mon.compliance.models import Framework, Control, Standard, StandardControlMapping, FrameworkWithControls, StandardWithControls, ControlWithStandards
from con_mon.utils.db import get_db


def _parse_datetime(date_string: str) -> Optional[datetime]:
    """Parse ISO datetime string, return None if invalid."""
    if not date_string or date_string == 'None':
        return None
    try:
        return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return None


def _parse_bool(value: str) -> bool:
    """Parse boolean string value."""
    if isinstance(value, bool):
        return value
    return str(value).lower() in ('true', '1', 'yes', 'on')


def load_frameworks_from_table_csv(csv_file_path: str = "data/csv/framework.csv") -> List[Framework]:
    """
    Load frameworks from exported framework table CSV file.
    
    Args:
        csv_file_path: Path to framework CSV file
        
    Returns:
        List of Framework objects
    """
    frameworks = []
    
    print(f"📁 Loading frameworks from CSV: {csv_file_path}")
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            for row in csv_reader:
                framework = Framework(
                    id=int(row['id']) if row['id'] else None,
                    name=row['name'],
                    version=row['version'] if row['version'] != 'None' else None,
                    description=row['description'] if row['description'] != 'None' else None,
                    issuing_organization=None,  # Not in exported table
                    publication_date=None,      # Not in exported table
                    status='active' if _parse_bool(row['active']) else 'inactive',
                    created_at=_parse_datetime(row['created_at']),
                    updated_at=_parse_datetime(row['updated_at'])
                )
                frameworks.append(framework)
        
        print(f"✅ Successfully loaded {len(frameworks)} frameworks from CSV")
        return frameworks
        
    except FileNotFoundError:
        print(f"❌ Framework CSV file not found: {csv_file_path}")
        raise
    except Exception as e:
        print(f"❌ Error loading frameworks from CSV: {e}")
        raise


def load_controls_from_table_csv(csv_file_path: str = "data/csv/control.csv") -> List[Control]:
    """
    Load controls from exported control table CSV file.
    
    Args:
        csv_file_path: Path to control CSV file
        
    Returns:
        List of Control objects
    """
    controls = []
    
    print(f"📁 Loading controls from CSV: {csv_file_path}")
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            for row in csv_reader:
                control = Control(
                    id=int(row['id']) if row['id'] else None,
                    framework_id=int(row['framework_id']),
                    control_id=row['control_name'],
                    name=row['control_long_name'] or row['control_name'],
                    description=row['control_text'] or row['control_discussion'] or '',
                    control_family=row['family_name'] if row['family_name'] != 'None' else None,
                    priority='medium',  # Default priority since not in DB
                    implementation_guidance=row['control_discussion'] if row['control_discussion'] != 'None' else None,
                    github_check_required=None,  # Not in DB schema
                    created_at=_parse_datetime(row['created_at']),
                    updated_at=_parse_datetime(row['updated_at'])
                )
                controls.append(control)
        
        print(f"✅ Successfully loaded {len(controls)} controls from CSV")
        return controls
        
    except FileNotFoundError:
        print(f"❌ Control CSV file not found: {csv_file_path}")
        raise
    except Exception as e:
        print(f"❌ Error loading controls from CSV: {e}")
        raise


def load_standards_from_table_csv(csv_file_path: str = "data/csv/standard.csv") -> List[Standard]:
    """
    Load standards from exported standard table CSV file.
    
    Args:
        csv_file_path: Path to standard CSV file
        
    Returns:
        List of Standard objects
    """
    standards = []
    
    print(f"📁 Loading standards from CSV: {csv_file_path}")
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            for row in csv_reader:
                standard = Standard(
                    id=int(row['id']) if row['id'] else None,
                    name=row['name'],
                    version=None,  # Not in DB schema
                    description=row['long_description'] or row['short_description'] if row.get('long_description') != 'None' else None,
                    issuing_organization=None,  # Not in DB schema
                    scope=None,  # Not in DB schema
                    status='active' if _parse_bool(row['active']) else 'inactive',
                    created_at=_parse_datetime(row['created_at']),
                    updated_at=_parse_datetime(row['updated_at'])
                )
                standards.append(standard)
        
        print(f"✅ Successfully loaded {len(standards)} standards from CSV")
        return standards
        
    except FileNotFoundError:
        print(f"❌ Standard CSV file not found: {csv_file_path}")
        raise
    except Exception as e:
        print(f"❌ Error loading standards from CSV: {e}")
        raise


def load_standard_control_mappings_from_table_csv(csv_file_path: str = "data/csv/standard_control_mapping.csv") -> List[StandardControlMapping]:
    """
    Load standard-control mappings from exported mapping table CSV file.
    
    Args:
        csv_file_path: Path to mapping CSV file
        
    Returns:
        List of StandardControlMapping objects
    """
    mappings = []
    
    print(f"📁 Loading mappings from CSV: {csv_file_path}")
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            for row in csv_reader:
                mapping = StandardControlMapping(
                    id=int(row['id']) if row['id'] else None,
                    standard_id=int(row['standard_id']),
                    control_id=int(row['control_id']),
                    mapping_type='direct',  # Default since not in DB
                    compliance_level=None,  # Not in DB schema
                    notes=row['additional_guidance'] if row.get('additional_guidance') != 'None' else None,
                    created_at=_parse_datetime(row['created_at']),
                    updated_at=_parse_datetime(row['updated_at'])
                )
                mappings.append(mapping)
        
        print(f"✅ Successfully loaded {len(mappings)} mappings from CSV")
        return mappings
        
    except FileNotFoundError:
        print(f"❌ Mapping CSV file not found: {csv_file_path}")
        raise
    except Exception as e:
        print(f"❌ Error loading mappings from CSV: {e}")
        raise


def populate_framework_data_from_csv(csv_dir: str = "data/csv") -> Tuple[List[FrameworkWithControls], List[StandardWithControls], List[StandardControlMapping]]:
    """
    Load and organize all framework data with relationships from CSV files.
    
    Args:
        csv_dir: Directory containing CSV files
        
    Returns:
        Tuple of (frameworks_with_controls, standards_with_controls, mappings)
    """
    print("🏗️  **Populating Framework Data from CSV Files**")
    print("=" * 50)
    
    # Load base data from CSV files
    frameworks = load_frameworks_from_table_csv(os.path.join(csv_dir, "framework.csv"))
    controls = load_controls_from_table_csv(os.path.join(csv_dir, "control.csv"))
    standards = load_standards_from_table_csv(os.path.join(csv_dir, "standard.csv"))
    mappings = load_standard_control_mappings_from_table_csv(os.path.join(csv_dir, "standard_control_mapping.csv"))
    
    # Organize controls by framework
    frameworks_with_controls = []
    for framework in frameworks:
        framework_controls = [c for c in controls if c.framework_id == framework.id]
        
        framework_with_controls = FrameworkWithControls(
            **framework.dict(),
            controls=framework_controls
        )
        frameworks_with_controls.append(framework_with_controls)
    
    # Organize controls by standard
    standards_with_controls = []
    for standard in standards:
        # Find controls mapped to this standard
        standard_control_ids = [m.control_id for m in mappings if m.standard_id == standard.id]
        standard_controls = [c for c in controls if c.id in standard_control_ids]
        
        standard_with_controls = StandardWithControls(
            **standard.dict(),
            controls=standard_controls
        )
        standards_with_controls.append(standard_with_controls)
    
    print(f"✅ Populated framework data from CSV files:")
    print(f"   • {len(frameworks_with_controls)} frameworks with controls")
    print(f"   • {len(standards_with_controls)} standards with controls")
    print(f"   • {len(mappings)} standard-control mappings")
    
    return frameworks_with_controls, standards_with_controls, mappings


def get_controls_with_standards_from_csv(csv_dir: str = "data/csv") -> List[ControlWithStandards]:
    """
    Load controls with their associated standards from CSV files.
    
    Args:
        csv_dir: Directory containing CSV files
    
    Returns:
        List of ControlWithStandards objects
    """
    # Load base data from CSV files
    frameworks = load_frameworks_from_table_csv(os.path.join(csv_dir, "framework.csv"))
    controls = load_controls_from_table_csv(os.path.join(csv_dir, "control.csv"))
    standards = load_standards_from_table_csv(os.path.join(csv_dir, "standard.csv"))
    mappings = load_standard_control_mappings_from_table_csv(os.path.join(csv_dir, "standard_control_mapping.csv"))
    
    # Organize standards by control
    controls_with_standards = []
    for control in controls:
        # Find standards mapped to this control
        control_standard_ids = [m.standard_id for m in mappings if m.control_id == control.id]
        control_standards = [s for s in standards if s.id in control_standard_ids]
        
        control_with_standards = ControlWithStandards(
            **control.dict(),
            standards=control_standards
        )
        controls_with_standards.append(control_with_standards)
    
    return controls_with_standards


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


def load_frameworks_from_db() -> Tuple[List[Framework], List[Control]]:
    """
    Load frameworks and controls from database tables.
    
    Returns:
        Tuple of (frameworks_list, controls_list)
    """
    db = get_db()
    
    print("🗄️  Loading framework data from database...")
    
    # Load frameworks from database
    frameworks_query = """
        SELECT id, name, version, description, 
               created_at, updated_at, active
        FROM framework 
        ORDER BY id
    """
    framework_rows = db.execute_query(frameworks_query)
    
    frameworks = []
    for row in framework_rows:
        framework = Framework(
            id=row['id'],
            name=row['name'],
            version=str(row['version']) if row['version'] is not None else None,
            description=row['description'],
            issuing_organization=None,  # Not in DB schema
            publication_date=None,      # Not in DB schema
            status='active' if row['active'] else 'inactive',
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
        frameworks.append(framework)
    
    # Load controls from database
    controls_query = """
        SELECT id, framework_id, control_name, family_name, 
               control_long_name, control_text, control_discussion,
               created_at, updated_at
        FROM control 
        ORDER BY framework_id, control_name
    """
    control_rows = db.execute_query(controls_query)
    
    controls = []
    for row in control_rows:
        control = Control(
            id=row['id'],
            framework_id=row['framework_id'],
            control_id=row['control_name'],
            name=row['control_long_name'] or row['control_name'],
            description=row['control_text'] or row['control_discussion'] or '',
            control_family=row['family_name'],
            priority='medium',  # Default priority since not in DB
            implementation_guidance=row['control_discussion'],
            github_check_required=None,  # Not in DB schema
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
        controls.append(control)
    
    print(f"✅ Successfully loaded from database:")
    print(f"   • {len(frameworks)} frameworks")
    print(f"   • {len(controls)} controls")
    
    return frameworks, controls


def load_standards_from_db() -> List[Standard]:
    """
    Load standards from database.
    
    Returns:
        List of Standard objects
    """
    db = get_db()
    
    standards_query = """
        SELECT id, name, short_description, long_description, 
               created_at, updated_at, active
        FROM standard 
        ORDER BY id
    """
    standard_rows = db.execute_query(standards_query)
    
    standards = []
    for row in standard_rows:
        standard = Standard(
            id=row['id'],
            name=row['name'],
            version=None,  # Not in DB schema
            description=row['long_description'] or row['short_description'],
            issuing_organization=None,  # Not in DB schema
            scope=None,  # Not in DB schema
            status='active' if row['active'] else 'inactive',
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
        standards.append(standard)
    
    print(f"✅ Successfully loaded {len(standards)} standards from database")
    return standards


def load_standard_control_mappings_from_db() -> List[StandardControlMapping]:
    """
    Load standard-control mappings from database.
    
    Returns:
        List of StandardControlMapping objects
    """
    db = get_db()
    
    mappings_query = """
        SELECT id, standard_id, control_id, 
               additional_selection_parameters, additional_guidance,
               created_at, updated_at
        FROM standard_control_mapping 
        ORDER BY standard_id, control_id
    """
    mapping_rows = db.execute_query(mappings_query)
    
    mappings = []
    for row in mapping_rows:
        mapping = StandardControlMapping(
            id=row['id'],
            standard_id=row['standard_id'],
            control_id=row['control_id'],
            mapping_type='direct',  # Default since not in DB
            compliance_level=None,  # Not in DB schema
            notes=row['additional_guidance'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
        mappings.append(mapping)
    
    print(f"✅ Successfully loaded {len(mappings)} standard-control mappings from database")
    return mappings


def populate_framework_data_from_db() -> Tuple[List[FrameworkWithControls], List[StandardWithControls], List[StandardControlMapping]]:
    """
    Load and organize all framework data with relationships from database.
    
    Returns:
        Tuple of (frameworks_with_controls, standards_with_controls, mappings)
    """
    print("🏗️  **Populating Framework Data from Database**")
    print("=" * 50)
    
    # Load base data from database
    frameworks, controls = load_frameworks_from_db()
    standards = load_standards_from_db()
    mappings = load_standard_control_mappings_from_db()
    
    # Organize controls by framework
    frameworks_with_controls = []
    for framework in frameworks:
        framework_controls = [c for c in controls if c.framework_id == framework.id]
        
        framework_with_controls = FrameworkWithControls(
            **framework.dict(),
            controls=framework_controls
        )
        frameworks_with_controls.append(framework_with_controls)
    
    # Organize controls by standard
    standards_with_controls = []
    for standard in standards:
        # Find controls mapped to this standard
        standard_control_ids = [m.control_id for m in mappings if m.standard_id == standard.id]
        standard_controls = [c for c in controls if c.id in standard_control_ids]
        
        standard_with_controls = StandardWithControls(
            **standard.dict(),
            controls=standard_controls
        )
        standards_with_controls.append(standard_with_controls)
    
    print(f"✅ Populated framework data from database:")
    print(f"   • {len(frameworks_with_controls)} frameworks with controls")
    print(f"   • {len(standards_with_controls)} standards with controls")
    print(f"   • {len(mappings)} standard-control mappings")
    
    return frameworks_with_controls, standards_with_controls, mappings


def get_controls_with_standards() -> List[ControlWithStandards]:
    """
    Load controls with their associated standards from database.
    
    Returns:
        List of ControlWithStandards objects
    """
    # Load base data from database
    frameworks, controls = load_frameworks_from_db()
    standards = load_standards_from_db()
    mappings = load_standard_control_mappings_from_db()
    
    # Organize standards by control
    controls_with_standards = []
    for control in controls:
        # Find standards mapped to this control
        control_standard_ids = [m.standard_id for m in mappings if m.control_id == control.id]
        control_standards = [s for s in standards if s.id in control_standard_ids]
        
        control_with_standards = ControlWithStandards(
            **control.dict(),
            standards=control_standards
        )
        controls_with_standards.append(control_with_standards)
    
    return controls_with_standards


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


def populate_framework_data() -> Tuple[List[FrameworkWithControls], List[StandardWithControls], List[StandardControlMapping]]:
    """
    Load and organize all framework data with relationships.
    Uses database loading by default, with CSV fallback.
    
    Returns:
        Tuple of (frameworks_with_controls, standards, mappings)
    """
    print("🏗️  **Populating Framework Data**")
    print("=" * 50)
    
    return populate_framework_data_from_db()


class BaseLoader(object):

    def _load_meta_data(self, model_class):
        """
        uses model_class and return the expected meta data
        """
        return table_name, fields

    def _load_data_from_connection(self, model_class, table_name, fields):
        """
        returns list of objects of model_class
        """
        raise NotImplementedError()

    def _load_data(self, model_class):
        table_name, fields = self._load_meta_data(model_class)
        return self._load_data_from_connection(model_class, table_name, fields)

    def load_frameworks(self) -> List[Framework]:
        """
        calls _load_data to get list of frameworks and return
        """
        return self._load_data(Framework)

    def load_standards(self) -> List[Standard]:
        """
        calls _load_data to get list of frameworks and return
        """
        return self._load_data(Standard)

    def load_controls(self) -> List[Control]:
        """
        calls _load_data to get list of frameworks and return
        """
        return self._load_data(Control)

    def list_framework_with_controls(
            self,
            frameworks: list[Framework],
            controls: list[Control],
    ) -> List[FrameworkWithControls]:
        """
        merges controls in frameworks
        """
        pass

    def list_controls_and_standards(
            self,
            standards: list[Standard],
            controls: list[Control],
            standard_control_mapping: list[StandardControlMapping],
    ) -> Tuple[List[StandardWithControls], List[ControlWithStandards]]:
        """
        return tuple of both lists of standards and controls
        """
        pass
