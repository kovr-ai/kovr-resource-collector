#!/usr/bin/env python3
"""
Export database tables to individual CSV files for backup and CSV-based loading.
"""

import sys
import os
import csv
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from con_mon.utils.db import get_db


def export_table_to_csv(table_name: str, output_dir: str = "data/csv") -> str:
    """
    Export a database table to a CSV file.
    
    Args:
        table_name: Name of the database table to export
        output_dir: Directory to save CSV files
        
    Returns:
        Path to the created CSV file
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get database connection
    db = get_db()
    
    # Query all data from the table
    query = f"SELECT * FROM {table_name} ORDER BY id"
    rows = db.execute_query(query)
    
    if not rows:
        print(f"⚠️  No data found in table '{table_name}'")
        return None
    
    # Create CSV file path
    csv_file_path = os.path.join(output_dir, f"{table_name}.csv")
    
    # Write to CSV
    with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
        # Get column names from the first row
        fieldnames = rows[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        # Write header
        writer.writeheader()
        
        # Write data rows
        for row in rows:
            # Convert datetime objects to strings for CSV compatibility
            csv_row = {}
            for key, value in row.items():
                if isinstance(value, datetime):
                    csv_row[key] = value.isoformat()
                else:
                    csv_row[key] = value
            writer.writerow(csv_row)
    
    print(f"✅ Exported {len(rows)} rows from '{table_name}' to {csv_file_path}")
    return csv_file_path


def main():
    """Export all compliance-related tables to CSV files."""
    
    print("📊 **DATABASE TO CSV EXPORTER**")
    print("=" * 60)
    print("Exporting compliance database tables to CSV files...")
    print()
    
    # Tables to export
    tables = [
        'framework',
        'control', 
        'standard',
        'standard_control_mapping'
    ]
    
    try:
        exported_files = []
        
        for table in tables:
            print(f"📋 Exporting table: {table}")
            csv_file = export_table_to_csv(table)
            if csv_file:
                exported_files.append(csv_file)
        
        print("\n" + "=" * 60)
        print("✅ **EXPORT COMPLETED**")
        print("=" * 60)
        print(f"📂 Exported {len(exported_files)} tables:")
        
        for file_path in exported_files:
            file_size = os.path.getsize(file_path)
            print(f"   • {os.path.basename(file_path)} ({file_size:,} bytes)")
        
        print(f"\n📁 CSV files saved in: data/csv/")
        print("🎯 Ready for CSV-based compliance data loading!")
        
    except Exception as e:
        print(f"\n❌ **Export failed:** {e}")
        print("Please ensure:")
        print("   • Database connection is available")
        print("   • Tables exist and are accessible")
        print("   • Write permissions for output directory")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 