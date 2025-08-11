#!/usr/bin/env python3
"""
Batch Add Checks to Database with LLM

This script processes all controls from data/csv/control.csv and generates
compliance checks using LLM, then inserts them into the database with
proper control-check mapping.

Usage:
    python batch_add_checks_in_db.py --resource-type github --connection-id 1
    python batch_add_checks_in_db.py --resource-type aws --connection-id 2 --limit 10
"""

import argparse
import csv
import logging
import time
from typing import Dict, Any, List, Optional
from pathlib import Path

from con_mon.utils.llm import get_llm_client
from con_mon.utils.db import get_db
from generate_checks_with_llm import (
    call_llm_for_check,
    process_response_to_check
)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def read_controls_from_csv(csv_path: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Read controls from CSV file.
    
    Args:
        csv_path: Path to the control.csv file
        limit: Maximum number of controls to process (None for all)
        
    Returns:
        List of control dictionaries
    """
    controls = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for i, row in enumerate(reader):
                if limit and i >= limit:
                    break
                    
                # Only process active controls
                if row.get('active', '').lower() == 'true':
                    controls.append({
                        'id': int(row['id']),
                        'control_name': row['control_name'],
                        'control_long_name': row['control_long_name'],
                        'control_text': row['control_text'],
                        'control_discussion': row.get('control_discussion', ''),
                        'family_name': row['family_name'],
                        'framework_id': int(row['framework_id'])
                    })
            
        logger.info(f"✅ Read {len(controls)} active controls from CSV")
        return controls
        
    except Exception as e:
        logger.error(f"❌ Failed to read controls from CSV: {e}")
        return []


def insert_check_to_database(check, control_id: int) -> Optional[int]:
    """
    Insert check into database using database library methods.
    
    Args:
        check: Check object to insert
        control_id: Control ID for mapping
        
    Returns:
        Generated check ID or None if failed
    """
    db = get_db()
    
    try:
        import json
        
        # Convert nested objects to JSON
        output_statements_json = json.dumps({
            "success": check.output_statements.success,
            "failure": check.output_statements.failure,
            "partial": check.output_statements.partial
        })
        
        fix_details_json = json.dumps({
            "description": check.fix_details.description,
            "instructions": check.fix_details.instructions,
            "estimated_date": check.fix_details.estimated_date,
            "automation_available": check.fix_details.automation_available
        })
        
        # Build metadata JSON
        metadata_json = json.dumps({
            "connection_id": check.connection_id,
            "field_path": check.field_path,
            "expected_value": check.expected_value,
            "resource_type": f"<class 'con_mon.resources.dynamic_models.{check.resource_type.__name__}'>" if check.resource_type else None,
            "tags": check.metadata.tags,
            "severity": check.metadata.severity,
            "category": check.metadata.category,
            "operation": {
                "name": check.operation.name.value,
                "logic": getattr(check.operation, '_original_custom_logic', '') or ""
            }
        })
        
        # Insert check using parameterized query
        insert_sql = """
        INSERT INTO checks (
            name, 
            description, 
            output_statements, 
            fix_details,
            created_by, 
            updated_by, 
            category, 
            metadata, 
            created_at, 
            updated_at, 
            is_deleted
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        ) RETURNING id;
        """
        
        # Execute insert with parameters
        with db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(insert_sql, (
                    check.name,
                    check.description or "",
                    output_statements_json,
                    fix_details_json,
                    check.created_by,
                    check.updated_by,
                    check.metadata.category,
                    metadata_json,
                    check.created_at,
                    check.updated_at,
                    check.is_deleted
                ))
                
                result = cursor.fetchone()
                check_id = result[0] if result else None
                
                if check_id:
                    # Insert the control-check mapping using parameterized query
                    mapping_sql = """
                    INSERT INTO control_checks_mapping (
                        control_id,
                        check_id,
                        created_at,
                        updated_at,
                        is_deleted
                    ) VALUES (
                        %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, false
                    );
                    """
                    
                    cursor.execute(mapping_sql, (control_id, check_id))
                    conn.commit()
                    
                    logger.info(f"✅ Inserted check ID {check_id} and mapping for control {control_id}")
                    return check_id
                else:
                    logger.error("❌ No check ID returned from INSERT")
                    return None
                    
    except Exception as e:
        logger.error(f"❌ Failed to insert check to database: {e}")
        import traceback
        traceback.print_exc()
        return None


def process_control(
    control_data: Dict[str, Any],
    resource_type: str,
    connection_id: int,
    delay_seconds: int = 2
) -> bool:
    """
    Process a single control to generate and insert check.
    
    Args:
        control_data: Control information
        resource_type: Target resource type
        connection_id: Connection ID
        delay_seconds: Delay between API calls
        
    Returns:
        True if successful, False otherwise
    """
    control_name = control_data['control_name']
    control_id = control_data['id']
    
    print(f"\n🔄 Processing Control: {control_name}")
    print(f"📋 Title: {control_data['control_long_name']}")
    print(f"🏷️ Family: {control_data['family_name']}")
    
    try:
        # Step 1: Call LLM to generate YAML
        yaml_content = call_llm_for_check(
            control_name=control_name,
            control_data=control_data,
            resource_type=resource_type,
            connection_id=connection_id
        )
        
        if not yaml_content:
            logger.error(f"❌ Failed to generate YAML for {control_name}")
            return False
        
        # Step 2: Process YAML to Check object
        check = process_response_to_check(
            yaml_content=yaml_content,
            control_name=control_name,
            control_data=control_data,
            resource_type=resource_type,
            connection_id=connection_id
        )
        
        if not check:
            logger.error(f"❌ Failed to create Check object for {control_name}")
            return False
        
        # Step 3: Insert to database directly
        generated_check_id = insert_check_to_database(check, control_id)
        
        if generated_check_id:
            print(f"✅ Successfully processed {control_name} -> Check ID: {generated_check_id}")
            
            # Add delay to avoid overwhelming the LLM API
            if delay_seconds > 0:
                print(f"⏳ Waiting {delay_seconds} seconds before next control...")
                time.sleep(delay_seconds)
            
            return True
        else:
            logger.error(f"❌ Failed to insert check for {control_name}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error processing control {control_name}: {e}")
        return False


def main():
    """Main batch processing function."""
    parser = argparse.ArgumentParser(description="Batch add checks to database using LLM")
    parser.add_argument("--resource-type", required=True,
                       choices=["github", "aws", "azure", "gcp"],
                       help="Target resource type")
    parser.add_argument("--connection-id", type=int, required=True,
                       help="Connection ID (1=GitHub, 2=AWS, etc.)")
    parser.add_argument("--csv-path", default="data/csv/control.csv",
                       help="Path to control.csv file")
    parser.add_argument("--limit", type=int,
                       help="Limit number of controls to process (for testing)")
    parser.add_argument("--delay", type=int, default=2,
                       help="Delay in seconds between API calls (default: 2)")
    parser.add_argument("--framework-id", type=int, default=2,
                       help="Framework ID to filter controls (default: 2 for NIST 800-53)")
    parser.add_argument("--dry-run", action="store_true",
                       help="Generate checks but don't insert to database")
    
    args = parser.parse_args()
    
    print("🚀 Batch Check Generation and Database Insertion")
    print("=" * 60)
    print(f"📁 CSV Path: {args.csv_path}")
    print(f"🎯 Resource Type: {args.resource_type}")
    print(f"🔗 Connection ID: {args.connection_id}")
    print(f"📊 Framework ID: {args.framework_id}")
    print(f"⏱️ API Delay: {args.delay} seconds")
    if args.limit:
        print(f"🔢 Limit: {args.limit} controls")
    if args.dry_run:
        print("🧪 DRY RUN MODE - No database insertions")
    print("=" * 60)
    
    # Check if CSV file exists
    csv_path = Path(args.csv_path)
    if not csv_path.exists():
        logger.error(f"❌ CSV file not found: {args.csv_path}")
        return 1
    
    # Test LLM connection
    try:
        client = get_llm_client()
        if not client.test_connection():
            logger.error("❌ LLM connection test failed")
            return 1
        print("✅ LLM connection verified")
    except Exception as e:
        logger.error(f"❌ LLM connection failed: {e}")
        return 1
    
    # Read controls from CSV
    all_controls = read_controls_from_csv(args.csv_path, args.limit)
    if not all_controls:
        logger.error("❌ No controls found to process")
        return 1
    
    # Filter by framework ID if specified
    controls = [c for c in all_controls if c['framework_id'] == args.framework_id]
    
    print(f"\n📋 Found {len(controls)} controls to process (Framework ID: {args.framework_id})")
    
    # Process controls
    successful = 0
    failed = 0
    
    for i, control in enumerate(controls, 1):
        print(f"\n{'='*20} Control {i}/{len(controls)} {'='*20}")
        
        if args.dry_run:
            print(f"🧪 DRY RUN: Would process {control['control_name']}")
            successful += 1
            continue
        
        success = process_control(
            control_data=control,
            resource_type=args.resource_type,
            connection_id=args.connection_id,
            delay_seconds=args.delay
        )
        
        if success:
            successful += 1
        else:
            failed += 1
            
        # Show progress
        print(f"📊 Progress: {successful} successful, {failed} failed")
    
    # Final summary
    print(f"\n🏁 BATCH PROCESSING COMPLETE")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {len(controls)}")
    print(f"📈 Success Rate: {(successful/len(controls)*100):.1f}%" if controls else "0%")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit(main()) 