#!/usr/bin/env python3
"""
Script to insert checks from checks.yaml into the database checks table.

This script reads the checks.yaml file and transforms the data to match
the database schema for the checks table.

Database Schema:
- id (character varying, NOT NULL) - Primary key
- name (character varying, NOT NULL) - Check name
- description (text, NOT NULL) - Check description  
- output_statements (jsonb, NOT NULL) - Success/failure messages
- fix_details (jsonb, NOT NULL) - Fix instructions
- created_by (character varying, NOT NULL) - Creator
- category (character varying, NOT NULL) - Check category
- metadata (jsonb, DEFAULT '{}') - Additional metadata
- updated_by (character varying, NOT NULL) - Last updater
- created_at (timestamp, DEFAULT CURRENT_TIMESTAMP) - Creation time
- updated_at (timestamp, DEFAULT CURRENT_TIMESTAMP) - Update time
- is_deleted (boolean, DEFAULT false) - Soft delete flag
"""

import yaml
import json
from datetime import datetime
from typing import Dict, Any, List
from con_mon.utils.db import get_db
from con_mon.utils.helpers import generate_static_result_messages
from con_mon.checks import get_loaded_checks


def transform_check_for_db(check) -> Dict[str, Any]:
    """
    Transform Check object to match database schema.
    
    Args:
        check: Check object from get_loaded_checks
        
    Returns:
        Dictionary with database-compatible fields
    """
    # Generate static messages using the helper function
    success_msg, partial_msg, failure_msg = generate_static_result_messages(check)
    
    # Build output_statements JSON using generated messages
    output_statements = {
        "success": success_msg,
        "failure": failure_msg,
        "partial": partial_msg
    }
    
    # Build fix_details JSON
    fix_details = {
        "description": f"Fix issues identified by the {check.name} check",
        "instructions": [
            "Review the check results to identify specific failures",
            "Apply appropriate remediation based on the check requirements",
            "Re-run the check to verify fixes"
        ],
        "automation_available": False,
        "estimated_time": "15-30 minutes"
    }
    
    # Build metadata JSON with check properties
    metadata = {
        "tags": check.tags or [],
        "severity": check.severity or 'medium',
        "field_path": check.field_path,
        "operation": {
            "name": check.operation.name.value if hasattr(check.operation.name, 'value') else str(check.operation.name)
        },
        "expected_value": check.expected_value,
        "resource_type": str(check.resource_type) if check.resource_type else None,
        "connection_id": check.connection_id
    }
    
    # Return database-compatible record
    return {
        "id": str(check.id),  # Convert to string as per DB schema
        "name": check.name,
        "description": check.description or "",
        "output_statements": json.dumps(output_statements),
        "fix_details": json.dumps(fix_details),
        "created_by": "system",
        "category": check.category or 'compliance',
        "metadata": json.dumps(metadata),
        "updated_by": "system"
    }

def create_checks_and_control_mapping_for_db(checks: list) -> List[Dict[str, Any]]:
    """
    Create many-to-many mapping records between checks and controls for database insertion.
    
    Args:
        checks: List of Check objects from get_loaded_checks
        
    Returns:
        List of mapping records ready for database insertion
    """
    mappings = []
    
    for check in checks:
        # Each check can have multiple control_ids
        if hasattr(check, 'control_ids') and check.control_ids:
            for control_id in check.control_ids:
                mapping = {
                    "control_id": control_id,
                    "check_id": str(check.id),  # Convert to string to match DB schema
                }
                mappings.append(mapping)
    
    print(f"✅ Created {len(mappings)} check-control mapping records")
    return mappings


def insert_checks_and_control_mapping_to_database(mappings: List[Dict[str, Any]], dry_run: bool = True) -> None:
    """
    Insert many-to-many mapping records between checks and controls into database.
    
    Args:
        mappings: List of mapping records with control_id and check_id
        dry_run: If True, only print what would be inserted without actual insertion
    """
    if not mappings:
        print("⚠️ No check-control mappings to insert")
        return
        
    if dry_run:
        print(f"\n🧪 DRY RUN MODE - Check-Control Mappings")
        print("=" * 60)
        
        # Group mappings by check_id for better display
        check_mappings = {}
        for mapping in mappings:
            check_id = mapping['check_id']
            if check_id not in check_mappings:
                check_mappings[check_id] = []
            check_mappings[check_id].append(mapping['control_id'])
        
        # Show first 5 checks and their control mappings
        for i, (check_id, control_ids) in enumerate(list(check_mappings.items())[:5]):
            print(f"\n📋 Check {check_id}:")
            print(f"   Controls: {control_ids}")
        
        if len(check_mappings) > 5:
            print(f"\n... and {len(check_mappings) - 5} more checks with mappings")
            
        print(f"\n📊 MAPPING SUMMARY:")
        print(f"   Total mapping records: {len(mappings)}")
        print(f"   Unique checks: {len(check_mappings)}")
        print(f"   Unique controls: {len(set(m['control_id'] for m in mappings))}")
        
        print(f"\n💡 To perform actual insertion, run with dry_run=False")
        return
    
    print(f"\n💾 INSERTING {len(mappings)} CHECK-CONTROL MAPPINGS INTO DATABASE...")
    print("=" * 80)
    
    db = get_db()
    
    # Prepare INSERT statement for control_checks_mapping table
    insert_sql = """
    INSERT INTO control_checks_mapping (
        control_id, check_id, created_at, updated_at, is_deleted
    ) VALUES (
        %s, %s, %s, %s, %s
    )
    ON CONFLICT (control_id, check_id) DO UPDATE SET
        updated_at = EXCLUDED.updated_at,
        is_deleted = EXCLUDED.is_deleted;
    """
    
    try:
        with db.get_connection() as conn:
            with conn.cursor() as cursor:
                current_time = datetime.now()
                
                # Prepare batch parameters
                batch_params = []
                for mapping in mappings:
                    params = (
                        mapping['control_id'],
                        mapping['check_id'],
                        current_time,  # created_at
                        current_time,  # updated_at
                        False  # is_deleted
                    )
                    batch_params.append(params)
                
                # Execute batch insert
                cursor.executemany(insert_sql, batch_params)
                inserted_count = cursor.rowcount
                
                conn.commit()
                
                print(f"✅ Successfully inserted/updated {inserted_count} check-control mappings")
                print(f"   • Operation: UPSERT (INSERT with ON CONFLICT UPDATE)")
                print(f"   • Timestamp: {current_time}")
                print(f"   • Table: control_checks_mapping")
                
    except Exception as e:
        print(f"❌ Check-control mapping insertion failed: {e}")
        raise

def insert_checks_to_database(db_records: List[Dict[str, Any]], dry_run: bool = True) -> None:
    """
    Insert check records into the database.
    
    Args:
        db_records: List of database-compatible check records
        dry_run: If True, only print what would be inserted without actual insertion
    """
    if dry_run:
        print(f"\n🧪 DRY RUN MODE - No actual database insertions will be performed")
        print("=" * 80)
        
        for i, record in enumerate(db_records[:5]):  # Show first 5 records
            print(f"\n📋 Record {i+1} (ID: {record['id']}):")
            print(f"   Name: {record['name']}")
            print(f"   Description: {record['description'][:100]}...")
            print(f"   Category: {record['category']}")
            print(f"   Output Statements: {json.loads(record['output_statements'])['success'][:60]}...")
            print(f"   Metadata Keys: {list(json.loads(record['metadata']).keys())}")
        
        if len(db_records) > 5:
            print(f"\n... and {len(db_records) - 5} more records")
            
        print(f"\n📊 SUMMARY:")
        print(f"   Total records to insert: {len(db_records)}")
        print(f"   Categories: {set(r['category'] for r in db_records)}")
        
        # Get connector types from metadata
        connector_types = set()
        for r in db_records:
            metadata = json.loads(r['metadata'])
            conn_id = metadata.get('connection_id', 'unknown')
            if conn_id == 1:
                connector_types.add('github')
            elif conn_id == 2:
                connector_types.add('aws')
            else:
                connector_types.add(f'connection_{conn_id}')
        print(f"   Connector types: {connector_types}")
        
        print(f"\n💡 To perform actual insertion, run with dry_run=False")
        return
    
    print(f"\n💾 INSERTING {len(db_records)} CHECKS INTO DATABASE...")
    print("=" * 80)
    
    db = get_db()
    
    # Prepare INSERT statement
    insert_sql = """
    INSERT INTO checks (
        id, name, description, output_statements, fix_details, 
        created_by, category, metadata, updated_by, created_at, updated_at, is_deleted
    ) VALUES (
        %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s, %s::jsonb, %s, %s, %s, %s
    )
    ON CONFLICT (id) DO UPDATE SET
        name = EXCLUDED.name,
        description = EXCLUDED.description,
        output_statements = EXCLUDED.output_statements,
        fix_details = EXCLUDED.fix_details,
        category = EXCLUDED.category,
        metadata = EXCLUDED.metadata,
        updated_by = EXCLUDED.updated_by,
        updated_at = EXCLUDED.updated_at;
    """
    
    try:
        with db.get_connection() as conn:
            with conn.cursor() as cursor:
                current_time = datetime.now()
                
                # Prepare batch parameters
                batch_params = []
                for record in db_records:
                    params = (
                        record['id'],
                        record['name'],
                        record['description'],
                        record['output_statements'],
                        record['fix_details'],
                        record['created_by'],
                        record['category'],
                        record['metadata'],
                        record['updated_by'],
                        current_time,  # created_at
                        current_time,  # updated_at
                        False  # is_deleted
                    )
                    batch_params.append(params)
                
                # Execute batch insert
                cursor.executemany(insert_sql, batch_params)
                inserted_count = cursor.rowcount
                
                conn.commit()
                
                print(f"✅ Successfully inserted/updated {inserted_count} checks")
                print(f"   • Operation: UPSERT (INSERT with ON CONFLICT UPDATE)")
                print(f"   • Timestamp: {current_time}")
                print(f"   • Created by: system")
                
    except Exception as e:
        print(f"❌ Database insertion failed: {e}")
        raise


def main():
    """Main function to load checks and insert into database."""
    print("🔄 CHECKS YAML TO DATABASE IMPORTER")
    print("=" * 80)

    # Step 1: Load checks using get_loaded_checks
    print("📖 Loading checks using get_loaded_checks()...")
    loaded_checks = get_loaded_checks()

    if not loaded_checks:
        print("❌ No checks found")
        return 1

    print(f"✅ Loaded {len(loaded_checks)} checks")

    # Step 2: Transform checks for database
    print(f"\n🔄 Transforming {len(loaded_checks)} checks for database schema...")
    db_records = []

    for _, check in loaded_checks.items():
        try:
            db_record = transform_check_for_db(check)
            db_records.append(db_record)
        except Exception as e:
            print(f"⚠️ Warning: Failed to transform check {check.id}: {e}")
            continue

    print(f"✅ Successfully transformed {len(db_records)} checks")

    # Step 3: Create check-control mappings
    print(f"\n🔗 Creating check-control mappings...")
    control_mappings = create_checks_and_control_mapping_for_db(loaded_checks)

    # Step 4: Insert into database (DRY RUN first)
    print(f"\n🧪 PERFORMING DRY RUN...")
    insert_checks_to_database(db_records, dry_run=True)

    if control_mappings:
        insert_checks_and_control_mapping_to_database(control_mappings, dry_run=True)

    # Ask user for confirmation to proceed with actual insertion
    print(f"\n❓ Do you want to proceed with actual database insertion? (y/N): ", end="")
    user_input = input().strip().lower()

    if user_input in ['y', 'yes']:
        # Insert checks first
        insert_checks_to_database(db_records, dry_run=False)

        # Then insert check-control mappings
        if control_mappings:
            insert_checks_and_control_mapping_to_database(control_mappings, dry_run=False)

        print(f"\n🎉 IMPORT COMPLETED SUCCESSFULLY!")
        print(f"   • Inserted {len(db_records)} checks")
        print(f"   • Inserted {len(control_mappings)} check-control mappings")
    else:
        print(f"\n❌ Import cancelled by user")
    
    return 0


if __name__ == "__main__":
    import sys
    exit_code = main()
    sys.exit(exit_code) 