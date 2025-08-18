#!/usr/bin/env python3
"""
Temporary script to parse through successful checks in generate_checks/prompts
Walks over the directory structure and parses YAML from output files using existing logic
Now includes CSV database insertion for checks.csv and control_checks_mapping.csv
"""

import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from con_mon.utils.llm.generate import get_provider_resources_mapping
from con_mon.connectors.models import ConnectorType
from con_mon.compliance.models import Check
from con_mon.utils.db import get_db
import yaml

def parse_yaml_from_output_file(output_file_path: Path) -> dict:
    """Parse YAML content from output file"""
    with open(output_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find YAML content - look for line starting with "checks:"
    lines = content.split('\n')
    yaml_start = None
    yaml_end = None

    for i, line in enumerate(lines):
        if line.strip().startswith('checks:'):
            yaml_start = i
            break

    if yaml_start is None:
        # Try alternative patterns
        for i, line in enumerate(lines):
            if 'checks:' in line and not line.strip().startswith('#'):
                yaml_start = i
                break

    if yaml_start is None:
        print(f"⚠️ Could not find 'checks:' line in {output_file_path}")
        # Debug: show first 10 lines
        print("   First 10 lines:")
        for i, line in enumerate(lines[:10]):
            print(f"   {i+1}: {line}")
        return None

    # Find the end (next line with ===, or end of file)
    for i in range(yaml_start + 1, len(lines)):
        if '=' * 10 in lines[i] or lines[i].strip().startswith('---'):
            yaml_end = i
            break

    # Extract YAML content
    if yaml_end:
        yaml_lines = lines[yaml_start:yaml_end]
    else:
        yaml_lines = lines[yaml_start:]

    # Clean up YAML lines - remove empty lines at the end
    while yaml_lines and not yaml_lines[-1].strip():
        yaml_lines.pop()

    yaml_content = '\n'.join(yaml_lines)

    print(f"      📝 Extracted YAML content ({len(yaml_lines)} lines)")
    print(f"         Preview: {yaml_content[:100]}...")

    # Parse YAML - this should be in the format "checks:\n- id: ..."
    try:
        parsed_yaml = yaml.safe_load(yaml_content)
    except yaml.YAMLError as ye:
        print(f"      ❌ YAML parsing error: {ye}")
        print(f"         YAML content:\n{yaml_content}")
        return None

    # Extract the first check from the checks array
    if parsed_yaml and 'checks' in parsed_yaml and parsed_yaml['checks']:
        check_data = parsed_yaml['checks'][0]  # Return the first (and usually only) check
        print(f"      ✅ Successfully parsed check: {check_data.get('id', 'unknown_id')}")
        return check_data
    else:
        print(f"⚠️ No checks found in YAML structure for {output_file_path}")
        print(f"   Parsed YAML keys: {list(parsed_yaml.keys()) if parsed_yaml else 'None'}")
        if parsed_yaml and 'checks' in parsed_yaml:
            print(f"   Checks array length: {len(parsed_yaml['checks'])}")
        return None

def serialize_for_csv(obj):
    """Custom serializer for complex objects to JSON strings for CSV storage"""
    if hasattr(obj, 'value'):  # Handle Enum types like ComparisonOperationEnum
        return obj.value  # Return the actual enum value (e.g., 'custom' instead of 'ComparisonOperationEnum.CUSTOM')
    elif hasattr(obj, 'model_dump'):  # Handle Pydantic models
        # Recursively serialize nested models with proper enum handling
        return serialize_nested_object(obj.model_dump())
    elif hasattr(obj, '__dict__'):  # Handle other objects
        return serialize_nested_object(obj.__dict__)
    elif isinstance(obj, dict):
        return serialize_nested_object(obj)
    elif isinstance(obj, list):
        return [serialize_for_csv(item) for item in obj]
    else:
        return str(obj)

def serialize_nested_object(obj_dict):
    """Recursively serialize nested objects, handling enums properly"""
    if isinstance(obj_dict, dict):
        result = {}
        for key, value in obj_dict.items():
            if hasattr(value, 'value'):  # Handle enum
                result[key] = value.value
            elif hasattr(value, 'model_dump'):  # Handle nested Pydantic model
                result[key] = serialize_nested_object(value.model_dump())
            elif isinstance(value, dict):
                result[key] = serialize_nested_object(value)
            elif isinstance(value, list):
                result[key] = [serialize_for_csv(item) for item in value]
            else:
                result[key] = value
        return result
    return obj_dict

def transform_check_for_database(check: Check) -> Dict[str, Any]:
    """
    Transform Check object for database storage (both PostgreSQL and CSV).
    Uses the same approach as batch_generate_checks.py for database-agnostic operations.
    
    Args:
        check: Check object to transform
        
    Returns:
        Dictionary with properly serialized JSONB fields
    """
    current_time = datetime.now().isoformat()
    
    # Convert Check object to database format with proper JSON serialization
    def serialize_for_json(obj):
        """Custom serializer for complex objects"""
        if hasattr(obj, 'value'):  # Handle Enum types like ComparisonOperationEnum
            return obj.value
        elif hasattr(obj, 'model_dump'):  # Handle Pydantic models
            return obj.model_dump()
        elif hasattr(obj, '__dict__'):  # Handle other objects
            return obj.__dict__
        else:
            return str(obj)
    
    # Convert complex fields to JSON with custom serializer (same as batch_generate_checks.py)
    output_statements_json = json.dumps(check.output_statements.model_dump(), default=serialize_for_json)
    fix_details_json = json.dumps(check.fix_details.model_dump(), default=serialize_for_json)
    metadata_json = json.dumps(check.metadata.model_dump(), default=serialize_for_json)
    
    return {
        'id': check.id,
        'name': check.name,
        'description': check.description,
        'output_statements': output_statements_json,  # JSON string for both PostgreSQL JSONB and CSV
        'fix_details': fix_details_json,              # JSON string for both PostgreSQL JSONB and CSV
        'metadata': metadata_json,                    # JSON string for both PostgreSQL JSONB and CSV
        'created_by': check.created_by,
        'category': check.category,
        'updated_by': check.updated_by,
        'created_at': check.created_at.isoformat() if hasattr(check.created_at, 'isoformat') else current_time,
        'updated_at': check.updated_at.isoformat() if hasattr(check.updated_at, 'isoformat') else current_time,
        'is_deleted': check.is_deleted
    }

def create_control_name_mapping():
    """
    Create a mapping from directory control names to actual control IDs.
    
    Returns:
        Dict mapping control_name -> [list of control IDs that match]
    """
    from con_mon.compliance.data_loader import ControlLoader
    
    # Load all controls
    control_loader = ControlLoader()
    controls = control_loader.load_all()
    
    # Create mapping from control names to control IDs
    control_mapping = {}
    
    for control in controls:
        control_name = control.control_name
        control_id = control.id
        
        # Direct mapping (exact match)
        if control_name not in control_mapping:
            control_mapping[control_name] = []
        control_mapping[control_name].append(control_id)
        
        # Also map base control name (e.g., "AC-2(1)" -> "AC-2")
        if '(' in control_name:
            base_name = control_name.split('(')[0]
            if base_name not in control_mapping:
                control_mapping[base_name] = []
            control_mapping[base_name].append(control_id)
    
    print(f"📋 Created control mapping for {len(control_mapping)} unique control names")
    print(f"   Total controls mapped: {sum(len(ids) for ids in control_mapping.values())}")
    
    # Show sample mappings
    sample_mappings = list(control_mapping.items())[:5]
    for name, ids in sample_mappings:
        print(f"   {name} -> {len(ids)} control(s): {ids[:3]}{'...' if len(ids) > 3 else ''}")
    
    return control_mapping

def extract_control_ids_from_path(output_file_path: Path, control_mapping: dict) -> List[int]:
    """
    Extract control IDs from the file path structure using the control mapping.
    
    Args:
        output_file_path: Path to the output file
        control_mapping: Dictionary mapping control names to control IDs
        
    Returns:
        List of control IDs that match the directory name
    """
    # Get control name from path (parent of parent of parent of file)
    control_name = output_file_path.parent.parent.parent.name

    # Look up control IDs for this control name
    if control_name in control_mapping:
        control_ids = control_mapping[control_name]
        print(f"      🎯 Mapped '{control_name}' to {len(control_ids)} control(s): {control_ids}")
        return control_ids
    else:
        print(f"      ⚠️ No mapping found for control name: '{control_name}'")
        return []

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
    # Verify check in checks.csv
    checks_results = db.execute('select', table_name='checks', where={'id': check_id})
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
    mapping_results = db.execute('select', table_name='control_checks_mapping',
                                 where={'check_id': check_id, 'control_id': control_id})
    if not mapping_results:
        print(f"      ❌ Mapping not found in control_checks_mapping.csv for check_id={check_id}, control_id={control_id}")
        return False

    mapping_record = mapping_results[0]
    print(f"      ✅ Mapping verified in CSV: control_id={mapping_record.get('control_id')}, check_id={mapping_record.get('check_id')}")
    print(f"         • Created at: {mapping_record.get('created_at')}")
    print(f"         • Is deleted: {mapping_record.get('is_deleted')}")

    return True

def insert_check_and_mapping_to_database(check: Check, control_id: int, db) -> bool:
    """
    Insert check into database and create mapping (works with both PostgreSQL and CSV)
    
    Args:
        check: Check object to insert
        control_id: Control ID for the mapping
        db: Database instance (PostgreSQL or CSV)
        
    Returns:
        True if successful, False otherwise
    """
    # Transform check for database storage (works with both PostgreSQL and CSV)
    check_data = transform_check_for_database(check)

    # Insert into database
    print(f"      📝 Inserting check into database: {check.id}")
    db.execute('insert', table_name='checks', update=check_data)

    # Create control-check mapping
    current_time = datetime.now().isoformat()
    mapping_data = {
        'control_id': control_id,
        'check_id': str(check.id),
        'created_at': current_time,
        'updated_at': current_time,
        'is_deleted': False
    }

    # Insert into control_checks_mapping
    print(f"      🔗 Creating control mapping: control_id={control_id}, check_id={check.id}")
    db.execute('insert', table_name='control_checks_mapping', update=mapping_data)

    # Verify the insertion was successful
    print(f"      🔍 Verifying insertion in database...")
    verification_success = verify_check_in_csv(str(check.id), control_id, db)

    if verification_success:
        print(f"      ✅ Database verification successful")
    else:
        print(f"      ❌ Database verification failed")

    return verification_success

def main():
    """Main function to walk through prompts and parse successful checks"""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Parse successful checks from generate_checks/prompts')
    parser.add_argument('--filter', type=str, help='Filter control directories by pattern (e.g., "AC-3-1-" for NIST 800-171, "GV." for CSF 2.0, "AC-" for NIST 800-53)')
    parser.add_argument('--limit', type=int, help='Limit number of controls to process')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    args = parser.parse_args()
    
    print("🚀 Parsing Successful Checks from generate_checks/prompts")
    print("💾 Inserting into Database (checks & control_checks_mapping tables)")
    if args.filter:
        print(f"🔍 Filtering controls with pattern: '{args.filter}'")
    if args.limit:
        print(f"📊 Limited to {args.limit} controls")
    print("=" * 80)
    
    # Setup paths
    prompts_dir = project_root / "data" / "generate_checks" / "prompts"
    
    if not prompts_dir.exists():
        print(f"❌ Prompts directory not found: {prompts_dir}")
        return
    
    # Get CSV database instance
    db = get_db()
    
    # Get provider resources mapping (reuse existing logic)
    provider_resources = get_provider_resources_mapping()
    
    # Create control name mapping
    control_mapping = create_control_name_mapping()
    
    # Statistics
    stats = {
        'total_controls': 0,
        'filtered_controls': 0,
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
    
    processed_count = 0
    start_time = datetime.now()
    
    for control_dir in control_dirs:
        if not control_dir.is_dir():
            continue
            
        control_name = control_dir.name
        stats['total_controls'] += 1
        
        # Apply filter if specified
        if args.filter and args.filter not in control_name:
            if args.verbose:
                print(f"⏭️  Skipping {control_name} (doesn't match filter '{args.filter}')")
            continue
        
        stats['filtered_controls'] += 1
        
        # Apply limit if specified
        if args.limit and processed_count >= args.limit:
            print(f"🛑 Reached limit of {args.limit} controls, stopping")
            break
        
        processed_count += 1
        
        # Calculate ETA
        elapsed_time = datetime.now() - start_time
        if processed_count > 1:
            avg_time_per_control = elapsed_time.total_seconds() / (processed_count - 1)
            remaining_controls = (args.limit or stats['filtered_controls']) - processed_count
            eta_seconds = avg_time_per_control * remaining_controls
            eta_minutes = int(eta_seconds // 60)
            eta_secs = int(eta_seconds % 60)
            eta_str = f"ETA: {eta_minutes}m {eta_secs}s"
        else:
            eta_str = "ETA: calculating..."
        
        print(f"\n📋 Processing control: {control_name} ({processed_count}/{args.limit or stats['filtered_controls']}) - {eta_str}")
        
        control_checks_added = 0
        
        # Walk through provider directories
        for provider_dir in control_dir.iterdir():
            if not provider_dir.is_dir():
                continue
                
            provider_name = provider_dir.name
            
            # Convert provider name to ConnectorType
            ConnectorType(provider_name.lower())
            
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

                        check = Check.from_row(yaml_data)

                        if check:
                            stats['successful_checks'] += 1
                            print(f"      ✅ Successfully created Check: {check.name}")
                            print(f"         ID: {check.id}")
                            print(f"         Description: {check.description[:100]}...")

                            # Extract control ID from path
                            control_ids = extract_control_ids_from_path(output_file, control_mapping)

                            # Insert into database
                            if control_ids: # Only insert if control_ids were found
                                for control_id in control_ids:
                                    if insert_check_and_mapping_to_database(check, control_id, db):
                                        stats['csv_insertion_success'] += 1
                                        stats['csv_verification_success'] += 1
                                        control_checks_added += 1
                                        print(f"      💾 Successfully inserted and verified in database for control_id={control_id}")
                                    else:
                                        stats['csv_insertion_errors'] += 1
                                        stats['csv_verification_errors'] += 1
                            else:
                                stats['csv_insertion_errors'] += 1
                                stats['csv_verification_errors'] += 1
                                print(f"      ❌ No control ID found for {output_file.name}, skipping insertion.")
                        else:
                            stats['check_creation_errors'] += 1
                            print(f"      ❌ Failed to create Check object")
                    else:
                        stats['parse_errors'] += 1
                        print(f"      ❌ Failed to parse YAML")
                else:
                    print(f"      ⚠️  No output file found")
        
        # Print control summary
        if control_checks_added > 0:
            total_checks_so_far = stats['csv_insertion_success']
            elapsed_total = datetime.now() - start_time
            checks_per_minute = (total_checks_so_far / elapsed_total.total_seconds()) * 60 if elapsed_total.total_seconds() > 0 else 0
            print(f"  📊 Control {control_name}: Added {control_checks_added} checks | Total: {total_checks_so_far} checks | Rate: {checks_per_minute:.1f} checks/min")
        else:
            print(f"  📊 Control {control_name}: No checks added")
    
    # Print final statistics
    print("\n" + "=" * 80)
    print("📊 PARSING & DATABASE INSERTION SUMMARY")
    print("=" * 80)
    print(f"Total controls found: {stats['total_controls']}")
    if args.filter:
        print(f"Controls matching filter: {stats['filtered_controls']}")
    print(f"Controls processed: {processed_count}")
    print(f"Total output files found: {stats['total_output_files']}")
    print(f"Successfully parsed YAML: {stats['successfully_parsed']}")
    print(f"Successfully created checks: {stats['successful_checks']}")
    print(f"Successfully inserted to database: {stats['csv_insertion_success']}")
    print(f"Parse errors: {stats['parse_errors']}")
    print(f"Check creation errors: {stats['check_creation_errors']}")
    print(f"Database insertion errors: {stats['csv_insertion_errors']}")
    print(f"Database verification success: {stats['csv_verification_success']}")
    print(f"Database verification errors: {stats['csv_verification_errors']}")
    
    if stats['total_output_files'] > 0:
        parse_success_rate = (stats['successfully_parsed'] / stats['total_output_files']) * 100
        check_success_rate = (stats['successful_checks'] / stats['total_output_files']) * 100
        db_success_rate = (stats['csv_insertion_success'] / stats['total_output_files']) * 100
        db_verification_rate = (stats['csv_verification_success'] / stats['total_output_files']) * 100
        print(f"Parse success rate: {parse_success_rate:.1f}%")
        print(f"Check creation success rate: {check_success_rate:.1f}%")
        print(f"Database insertion success rate: {db_success_rate:.1f}%")
        print(f"Database verification success rate: {db_verification_rate:.1f}%")
    
    if hasattr(db, '_csv_directory'):
        print(f"\n📁 CSV files location: {db._csv_directory}")
    print("✅ Parsing and database insertion complete!")

if __name__ == "__main__":
    main() 