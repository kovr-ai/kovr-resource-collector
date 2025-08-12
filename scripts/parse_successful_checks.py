#!/usr/bin/env python3
"""
Temporary script to parse through successful checks in generate_checks/prompts
Walks over the directory structure and parses YAML from output files using existing logic
Now includes CSV database insertion for checks.csv and control_checks_mapping.csv
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set environment to use CSV database
os.environ['DB_USE_POSTGRES'] = 'false'

from con_mon_v2.utils.llm.generate import get_provider_resources_mapping
from con_mon_v2.connectors.models import ConnectorType
from con_mon_v2.compliance.models import Check
from con_mon_v2.utils.db import get_db
import yaml

def parse_yaml_from_output_file(output_file_path: Path) -> dict:
    """Parse YAML content from output file"""
    try:
        with open(output_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Find YAML content - look for line starting with "checks:"
        lines = content.split('\n')
        yaml_start = None
        yaml_end = None
        
        for i, line in enumerate(lines):
            if line.startswith('checks:'):
                yaml_start = i
                break
        
        if yaml_start is None:
            print(f"⚠️ Could not find 'checks:' line in {output_file_path}")
            return None
            
        # Find the end (next line with ===)
        for i in range(yaml_start, len(lines)):
            if '=' * 80 in lines[i]:
                yaml_end = i
                break
                
        # Extract YAML content
        yaml_content = '\n'.join(lines[yaml_start:yaml_end]) if yaml_end else '\n'.join(lines[yaml_start:])
        
        # Parse YAML - this should be in the format "checks:\n- id: ..."
        parsed_yaml = yaml.safe_load(yaml_content)
        
        # Extract the first check from the checks array
        if parsed_yaml and 'checks' in parsed_yaml and parsed_yaml['checks']:
            return parsed_yaml['checks'][0]  # Return the first (and usually only) check
        else:
            print(f"⚠️ No checks found in YAML structure for {output_file_path}")
            return None
        
    except Exception as e:
        print(f"❌ Error parsing {output_file_path}: {e}")
        return None

def serialize_for_csv(obj):
    """Custom serializer for complex objects to JSON strings for CSV storage"""
    if hasattr(obj, 'value'):  # Handle Enum types like ComparisonOperationEnum
        return obj.value
    elif hasattr(obj, 'model_dump'):  # Handle Pydantic models
        return obj.model_dump()
    elif hasattr(obj, '__dict__'):  # Handle other objects
        return obj.__dict__
    else:
        return str(obj)

def transform_check_for_csv(check: Check) -> Dict[str, Any]:
    """
    Transform Check object to match CSV schema with flattened nested fields.
    
    Args:
        check: Check object to transform
        
    Returns:
        Dictionary with CSV-compatible flattened fields
    """
    current_time = datetime.now().isoformat()
    
    # Serialize nested objects to JSON strings
    output_statements_json = json.dumps(check.output_statements.model_dump(), default=serialize_for_csv)
    fix_details_json = json.dumps(check.fix_details.model_dump(), default=serialize_for_csv)
    metadata_json = json.dumps(check.metadata.model_dump(), default=serialize_for_csv)
    
    # Parse the JSON to get individual fields for flattened CSV structure
    output_statements = check.output_statements.model_dump()
    fix_details = check.fix_details.model_dump()
    metadata = check.metadata.model_dump()
    
    return {
        "id": str(check.id),  # Ensure ID is string for CSV
        "name": check.name,
        "description": check.description,
        
        # Flattened output_statements fields
        "output_statements.failure": output_statements.get('failure', ''),
        "output_statements.partial": output_statements.get('partial', ''),
        "output_statements.success": output_statements.get('success', ''),
        
        # Flattened fix_details fields
        "fix_details.description": fix_details.get('description', ''),
        "fix_details.instructions": json.dumps(fix_details.get('instructions', []), default=serialize_for_csv),
        "fix_details.estimated_time": fix_details.get('estimated_time', ''),
        "fix_details.automation_available": fix_details.get('automation_available', False),
        
        # Regular fields
        "created_by": check.created_by,
        "category": check.category,
        "updated_by": check.updated_by,
        "created_at": check.created_at.isoformat() if hasattr(check.created_at, 'isoformat') else current_time,
        "updated_at": check.updated_at.isoformat() if hasattr(check.updated_at, 'isoformat') else current_time,
        "is_deleted": check.is_deleted,
        
        # Flattened metadata fields
        "metadata.tags": json.dumps(metadata.get('tags', []), default=serialize_for_csv),
        "metadata.category": metadata.get('category', ''),
        "metadata.severity": metadata.get('severity', ''),
        "metadata.operation.name": metadata.get('operation', {}).get('name', ''),
        "metadata.operation.logic": metadata.get('operation', {}).get('logic', ''),
        "metadata.field_path": metadata.get('field_path', ''),
        "metadata.connection_id": metadata.get('connection_id', 1),
        "metadata.resource_type": metadata.get('resource_type', ''),
        "metadata.expected_value": json.dumps(metadata.get('expected_value'), default=serialize_for_csv) if metadata.get('expected_value') is not None else None,
    }

def extract_control_id_from_path(output_file_path: Path) -> Optional[int]:
    """
    Extract control ID from the file path structure.
    Assumes path like: .../prompts/{control_name}/{provider}/{resource}/output_...
    
    For now, we'll use a simple mapping or return a default control ID.
    In a real implementation, you'd want to map control names to actual control IDs.
    """
    try:
        # Get control name from path (parent of parent of parent of file)
        control_name = output_file_path.parent.parent.parent.name
        
        # For demo purposes, return a hash-based ID or default
        # In real implementation, you'd query the control table
        control_id = hash(control_name) % 1000  # Simple hash to get a consistent ID
        return abs(control_id)
    except:
        return 1  # Default control ID

def verify_check_in_csv(check_id: str, control_id: int, db) -> bool:
    """
    Verify that a check and its mapping were properly stored in CSV files.
    
    Args:
        check_id: ID of the check to verify
        control_id: Control ID to verify in mapping
        db: CSV database instance
        
    Returns:
        True if both check and mapping are found and valid, False otherwise
    """
    try:
        # Verify check in checks.csv
        checks_results = db.execute_query('checks', conditions={'id': check_id})
        if not checks_results:
            print(f"      ❌ Check {check_id} not found in checks.csv")
            return False
        
        check_record = checks_results[0]
        print(f"      ✅ Check verified in CSV: {check_record.get('name', 'Unknown')}")
        print(f"         • ID: {check_record.get('id')}")
        print(f"         • Description: {check_record.get('description', '')[:80]}...")
        print(f"         • Category: {check_record.get('category')}")
        print(f"         • Created by: {check_record.get('created_by')}")
        
        # Verify nested JSONB fields were properly stored and can be parsed
        metadata_tags = check_record.get('metadata.tags')
        if metadata_tags:
            print(f"         • Tags: {metadata_tags}")
        
        # Verify mapping in control_checks_mapping.csv
        mapping_results = db.execute_query('control_checks_mapping', 
                                         conditions={'check_id': check_id, 'control_id': control_id})
        if not mapping_results:
            print(f"      ❌ Mapping not found in control_checks_mapping.csv for check_id={check_id}, control_id={control_id}")
            return False
        
        mapping_record = mapping_results[0]
        print(f"      ✅ Mapping verified in CSV: control_id={mapping_record.get('control_id')}, check_id={mapping_record.get('check_id')}")
        print(f"         • Created at: {mapping_record.get('created_at')}")
        print(f"         • Is deleted: {mapping_record.get('is_deleted')}")
        
        return True
        
    except Exception as e:
        print(f"      ❌ Error verifying check {check_id} in CSV: {e}")
        return False

def insert_check_and_mapping_to_csv(check: Check, control_id: int, db) -> bool:
    """
    Insert check into checks.csv and create mapping in control_checks_mapping.csv
    
    Args:
        check: Check object to insert
        control_id: Control ID for the mapping
        db: CSV database instance
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Transform check for CSV storage
        check_data = transform_check_for_csv(check)
        
        # Insert into checks.csv
        print(f"      📝 Inserting check into CSV: {check.id}")
        db.execute_insert('checks', check_data)
        
        # Create control-check mapping
        current_time = datetime.now().isoformat()
        mapping_data = {
            'control_id': control_id,
            'check_id': str(check.id),
            'created_at': current_time,
            'updated_at': current_time,
            'is_deleted': False
        }
        
        # Insert into control_checks_mapping.csv
        print(f"      🔗 Creating control mapping: control_id={control_id}, check_id={check.id}")
        db.execute_insert('control_checks_mapping', mapping_data)
        
        # Verify the insertion was successful
        print(f"      🔍 Verifying insertion in CSV files...")
        verification_success = verify_check_in_csv(str(check.id), control_id, db)
        
        if verification_success:
            print(f"      ✅ CSV verification successful")
        else:
            print(f"      ❌ CSV verification failed")
            
        return verification_success
        
    except Exception as e:
        print(f"      ❌ Failed to insert check {check.id} to CSV: {e}")
        return False

def create_csv_tables_if_needed(db):
    """Create CSV tables if they don't exist"""
    try:
        # Check if checks.csv exists, if not create with headers
        if not db._table_exists('checks'):
            print("📋 Creating checks.csv table...")
            checks_columns = [
                'id', 'name', 'description',
                'output_statements.failure', 'output_statements.partial', 'output_statements.success',
                'fix_details.description', 'fix_details.instructions', 'fix_details.estimated_time', 'fix_details.automation_available',
                'created_by', 'category', 
                'metadata.tags', 'metadata.category', 'metadata.severity', 
                'metadata.operation.name', 'metadata.operation.logic', 'metadata.field_path', 
                'metadata.connection_id', 'metadata.resource_type', 'metadata.expected_value',
                'updated_by', 'created_at', 'updated_at', 'is_deleted'
            ]
            db.create_table('checks', checks_columns)
        
        # Check if control_checks_mapping.csv exists, if not create with headers
        if not db._table_exists('control_checks_mapping'):
            print("📋 Creating control_checks_mapping.csv table...")
            mapping_columns = ['control_id', 'check_id', 'created_at', 'updated_at', 'is_deleted']
            db.create_table('control_checks_mapping', mapping_columns)
            
    except Exception as e:
        print(f"❌ Error creating CSV tables: {e}")
        raise

def main():
    """Main function to walk through prompts and parse successful checks"""
    
    print("🚀 Parsing Successful Checks from generate_checks/prompts")
    print("💾 Inserting into CSV Database (checks.csv & control_checks_mapping.csv)")
    print("=" * 80)
    
    # Setup paths
    prompts_dir = project_root / "data" / "generate_checks" / "prompts"
    
    if not prompts_dir.exists():
        print(f"❌ Prompts directory not found: {prompts_dir}")
        return
    
    # Get CSV database instance
    db = get_db()
    print(f"📁 CSV Database directory: {db._csv_directory}")
    
    # Create CSV tables if needed
    create_csv_tables_if_needed(db)
    
    # Get provider resources mapping (reuse existing logic)
    provider_resources = get_provider_resources_mapping()
    
    # Statistics
    stats = {
        'total_controls': 0,
        'total_output_files': 0,
        'successfully_parsed': 0,
        'parse_errors': 0,
        'check_creation_errors': 0,
        'successful_checks': 0,
        'csv_insertion_success': 0,
        'csv_insertion_errors': 0,
        'csv_verification_success': 0,
        'csv_verification_errors': 0
    }
    
    # Walk through control directories
    control_dirs = sorted(prompts_dir.iterdir())  # Process all controls
    
    for control_dir in control_dirs:
        if not control_dir.is_dir():
            continue
            
        control_name = control_dir.name
        stats['total_controls'] += 1
        
        print(f"\n📋 Processing control: {control_name}")
        
        # Walk through provider directories
        for provider_dir in control_dir.iterdir():
            if not provider_dir.is_dir():
                continue
                
            provider_name = provider_dir.name
            
            # Convert provider name to ConnectorType
            try:
                connector_type = ConnectorType(provider_name.lower())
            except ValueError:
                print(f"  ⚠️  Unknown provider: {provider_name}")
                continue
            
            print(f"  🔗 Provider: {provider_name}")
            
            # Walk through resource directories
            for resource_dir in provider_dir.iterdir():
                if not resource_dir.is_dir():
                    continue
                    
                resource_type = resource_dir.name
                print(f"    📦 Resource: {resource_type}")
                
                # Look for output file
                output_file = resource_dir / f"output_{control_name}_{provider_name}_{resource_type}.txt"
                
                if output_file.exists():
                    stats['total_output_files'] += 1
                    print(f"      📄 Found output file: {output_file.name}")
                    
                    # Parse YAML from output file
                    yaml_data = parse_yaml_from_output_file(output_file)
                    
                    if yaml_data:
                        stats['successfully_parsed'] += 1
                        print(f"      ✅ Successfully parsed YAML")
                        
                        # Try to create Check object
                        # Add missing datetime fields that from_row expects
                        yaml_data['created_at'] = datetime.now()
                        yaml_data['updated_at'] = datetime.now()
                        
                        try:
                            check = Check.from_row(yaml_data)
                            
                            if check:
                                stats['successful_checks'] += 1
                                print(f"      ✅ Successfully created Check: {check.name}")
                                print(f"         ID: {check.id}")
                                print(f"         Description: {check.description[:100]}...")
                                
                                # Extract control ID from path
                                control_id = extract_control_id_from_path(output_file)
                                
                                # Insert into CSV database
                                if insert_check_and_mapping_to_csv(check, control_id, db):
                                    stats['csv_insertion_success'] += 1
                                    stats['csv_verification_success'] += 1
                                    print(f"      💾 Successfully inserted and verified in CSV database")
                                else:
                                    stats['csv_insertion_errors'] += 1
                                    stats['csv_verification_errors'] += 1
                            else:
                                stats['check_creation_errors'] += 1
                                print(f"      ❌ Failed to create Check object")
                        except Exception as e:
                            stats['check_creation_errors'] += 1
                            print(f"      ❌ Error creating Check object: {e}")
                    else:
                        stats['parse_errors'] += 1
                        print(f"      ❌ Failed to parse YAML")
                else:
                    print(f"      ⚠️  No output file found")
    
    # Print final statistics
    print("\n" + "=" * 80)
    print("📊 PARSING & CSV INSERTION SUMMARY")
    print("=" * 80)
    print(f"Total controls processed: {stats['total_controls']}")
    print(f"Total output files found: {stats['total_output_files']}")
    print(f"Successfully parsed YAML: {stats['successfully_parsed']}")
    print(f"Successfully created checks: {stats['successful_checks']}")
    print(f"Successfully inserted to CSV: {stats['csv_insertion_success']}")
    print(f"Parse errors: {stats['parse_errors']}")
    print(f"Check creation errors: {stats['check_creation_errors']}")
    print(f"CSV insertion errors: {stats['csv_insertion_errors']}")
    print(f"CSV verification success: {stats['csv_verification_success']}")
    print(f"CSV verification errors: {stats['csv_verification_errors']}")
    
    if stats['total_output_files'] > 0:
        parse_success_rate = (stats['successfully_parsed'] / stats['total_output_files']) * 100
        check_success_rate = (stats['successful_checks'] / stats['total_output_files']) * 100
        csv_success_rate = (stats['csv_insertion_success'] / stats['total_output_files']) * 100
        csv_verification_rate = (stats['csv_verification_success'] / stats['total_output_files']) * 100
        print(f"Parse success rate: {parse_success_rate:.1f}%")
        print(f"Check creation success rate: {check_success_rate:.1f}%")
        print(f"CSV insertion success rate: {csv_success_rate:.1f}%")
        print(f"CSV verification success rate: {csv_verification_rate:.1f}%")
    
    print(f"\n📁 CSV files location: {db._csv_directory}")
    print("✅ Parsing and CSV insertion complete!")

if __name__ == "__main__":
    main() 