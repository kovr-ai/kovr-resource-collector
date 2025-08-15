#!/usr/bin/env python3
"""
Data Manager Script - Import/Export PostgreSQL tables to/from CSV

This script provides a command-line interface to import and export data
between PostgreSQL database and CSV files using the data loaders.

Usage Examples:
    # Export all tables
    python data_manager.py export --all
    
    # Export specific tables
    python data_manager.py export --tables connections checks
    
    # Import all tables with updates
    python data_manager.py import --all --update
    
    # Import specific table without updates
    python data_manager.py import --tables connections --no-update
    
    # List available tables
    python data_manager.py list
"""

import argparse
import sys
from typing import List, Dict, Type
from pathlib import Path

from con_mon_v2.utils.db.pgs import get_db as get_pgs_db
from con_mon_v2.compliance.data_loader.base import BaseLoader
from con_mon_v2.compliance.data_loader import (
    ChecksLoader,
    ConnectionLoader,
    FrameworkLoader,
    ControlLoader,
    StandardLoader,
    StandardControlMappingLoader,
    ConMonResultLoader,
    ConMonResultHistoryLoader
)

# Available loaders mapped by table name
AVAILABLE_LOADERS: Dict[str, Type[BaseLoader]] = {
    'checks': ChecksLoader,
    'connections': ConnectionLoader,
    'frameworks': FrameworkLoader,
    'controls': ControlLoader,
    'standards': StandardLoader,
    'standard_control_mappings': StandardControlMappingLoader,
    'con_mon_results': ConMonResultLoader,
    'con_mon_results_history': ConMonResultHistoryLoader,
}


def get_loader_instance(table_name: str) -> BaseLoader:
    """Get a loader instance for the specified table."""
    if table_name not in AVAILABLE_LOADERS:
        raise ValueError(f"Unknown table: {table_name}. Available: {list(AVAILABLE_LOADERS.keys())}")
    
    loader_class = AVAILABLE_LOADERS[table_name]
    loader = loader_class()
    
    # Force PostgreSQL database for consistency
    loader.db = get_pgs_db()
    
    return loader


def list_tables():
    """List all available tables."""
    print("📋 Available tables:")
    for table_name in AVAILABLE_LOADERS.keys():
        print(f"   • {table_name}")


def export_table(table_name: str, where_clause: str = None) -> str:
    """Export a single table to CSV."""
    try:
        loader = get_loader_instance(table_name)
        
        print(f"📤 Exporting table '{table_name}'...")
        
        # Use where_clause if provided, otherwise use loader defaults
        if where_clause:
            csv_path = loader.export_to_csv(where_clause=where_clause)
        else:
            csv_path = loader.export_to_csv()
        
        print(f"✅ Exported '{table_name}' to: {csv_path}")
        return csv_path
        
    except Exception as e:
        print(f"❌ Failed to export '{table_name}': {e}")
        raise


def import_table(table_name: str, update_existing: bool = True, batch_size: int = 100) -> int:
    """Import a single table from CSV."""
    try:
        loader = get_loader_instance(table_name)
        
        print(f"📥 Importing table '{table_name}'...")
        
        rows_imported = loader.import_from_csv(
            update_existing=update_existing,
            batch_size=batch_size
        )
        
        print(f"✅ Imported {rows_imported} rows to '{table_name}'")
        return rows_imported
        
    except Exception as e:
        print(f"❌ Failed to import '{table_name}': {e}")
        raise


def export_tables(table_names: List[str], where_clause: str = None):
    """Export multiple tables."""
    print(f"📤 Starting export of {len(table_names)} table(s)...")
    
    results = {}
    for table_name in table_names:
        try:
            csv_path = export_table(table_name, where_clause)
            results[table_name] = {'status': 'success', 'path': csv_path}
        except Exception as e:
            results[table_name] = {'status': 'error', 'error': str(e)}
    
    # Summary
    print(f"\n📊 Export Summary:")
    success_count = sum(1 for r in results.values() if r['status'] == 'success')
    error_count = len(results) - success_count
    
    print(f"   • Successful: {success_count}")
    print(f"   • Failed: {error_count}")
    
    if error_count > 0:
        print(f"\n❌ Failed tables:")
        for table_name, result in results.items():
            if result['status'] == 'error':
                print(f"   • {table_name}: {result['error']}")
    
    return results


def import_tables(table_names: List[str], update_existing: bool = True, batch_size: int = 100):
    """Import multiple tables."""
    print(f"📥 Starting import of {len(table_names)} table(s)...")
    
    results = {}
    total_rows = 0
    
    for table_name in table_names:
        try:
            rows_imported = import_table(table_name, update_existing, batch_size)
            results[table_name] = {'status': 'success', 'rows': rows_imported}
            total_rows += rows_imported
        except Exception as e:
            results[table_name] = {'status': 'error', 'error': str(e)}
    
    # Summary
    print(f"\n📊 Import Summary:")
    success_count = sum(1 for r in results.values() if r['status'] == 'success')
    error_count = len(results) - success_count
    
    print(f"   • Successful: {success_count}")
    print(f"   • Failed: {error_count}")
    print(f"   • Total rows imported: {total_rows}")
    
    if error_count > 0:
        print(f"\n❌ Failed tables:")
        for table_name, result in results.items():
            if result['status'] == 'error':
                print(f"   • {table_name}: {result['error']}")
    
    return results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Import/Export PostgreSQL tables to/from CSV",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s list                                    # List available tables
  %(prog)s export --all                           # Export all tables
  %(prog)s export --tables connections checks     # Export specific tables
  %(prog)s export --tables checks --where "is_deleted = false"  # Export with filter
  %(prog)s import --all --update                  # Import all with updates
  %(prog)s import --tables connections --no-update # Import without updates
  %(prog)s import --tables checks --batch-size 50 # Import with custom batch size
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List available tables')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export tables to CSV')
    export_group = export_parser.add_mutually_exclusive_group(required=True)
    export_group.add_argument('--all', action='store_true', help='Export all tables')
    export_group.add_argument('--tables', nargs='+', help='Specific tables to export')
    export_parser.add_argument('--where', help='WHERE clause for filtering data')
    
    # Import command
    import_parser = subparsers.add_parser('import', help='Import tables from CSV')
    import_group = import_parser.add_mutually_exclusive_group(required=True)
    import_group.add_argument('--all', action='store_true', help='Import all tables')
    import_group.add_argument('--tables', nargs='+', help='Specific tables to import')
    
    update_group = import_parser.add_mutually_exclusive_group()
    update_group.add_argument('--update', action='store_true', default=True, 
                             help='Update existing records (default)')
    update_group.add_argument('--no-update', action='store_false', dest='update',
                             help='Do not update existing records')
    
    import_parser.add_argument('--batch-size', type=int, default=100,
                              help='Batch size for import operations (default: 100)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        if args.command == 'list':
            list_tables()
            
        elif args.command == 'export':
            if args.all:
                table_names = list(AVAILABLE_LOADERS.keys())
            else:
                table_names = args.tables
            
            # Validate table names
            invalid_tables = [t for t in table_names if t not in AVAILABLE_LOADERS]
            if invalid_tables:
                print(f"❌ Invalid table names: {invalid_tables}")
                print(f"Available tables: {list(AVAILABLE_LOADERS.keys())}")
                return 1
            
            export_tables(table_names, args.where)
            
        elif args.command == 'import':
            if args.all:
                table_names = list(AVAILABLE_LOADERS.keys())
            else:
                table_names = args.tables
            
            # Validate table names
            invalid_tables = [t for t in table_names if t not in AVAILABLE_LOADERS]
            if invalid_tables:
                print(f"❌ Invalid table names: {invalid_tables}")
                print(f"Available tables: {list(AVAILABLE_LOADERS.keys())}")
                return 1
            
            import_tables(table_names, args.update, args.batch_size)
        
        return 0
        
    except KeyboardInterrupt:
        print(f"\n⚠️ Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main()) 