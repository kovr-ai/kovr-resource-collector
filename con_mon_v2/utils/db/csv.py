"""
CSV Database singleton for file-based operations in con_mon.

Provides a singleton pattern for CSV file operations with methods for executing
CRUD operations on CSV files stored in data/csv/ folder.
"""
import os
import csv
import json
import pandas as pd
from typing import Optional, List, Dict, Any, Union
from contextlib import contextmanager
import logging
from pathlib import Path
import shutil
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CSVDatabase:
    """
    Singleton class for CSV file database operations.
    
    Manages CRUD operations on CSV files where each file represents a table.
    Files are stored in data/csv/ directory.
    """
    
    _instance: Optional['CSVDatabase'] = None
    _csv_directory: Optional[Path] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'CSVDatabase':
        if cls._instance is None:
            cls._instance = super(CSVDatabase, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._initialized = True
            self._setup_csv_directory()
    
    def _setup_csv_directory(self):
        """Initialize the CSV directory path and ensure it exists."""
        try:
            # Set up CSV directory path
            self._csv_directory = Path("data/csv")
            
            # Create directory if it doesn't exist
            self._csv_directory.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"✅ CSV database directory initialized: {self._csv_directory.absolute()}")
            
        except Exception as e:
            logger.warning(f"⚠️ CSV directory setup failed: {e}")
            logger.info("💡 CSV operations will be unavailable until directory is accessible")
            self._csv_directory = None
    
    def _get_table_path(self, table_name: str) -> Path:
        """Get the file path for a given table name."""
        if not self._csv_directory:
            raise Exception("CSV directory not initialized")
        
        # Ensure table name ends with .csv
        if not table_name.endswith('.csv'):
            table_name += '.csv'
        
        return self._csv_directory / table_name
    
    def _table_exists(self, table_name: str) -> bool:
        """Check if a table (CSV file) exists."""
        try:
            table_path = self._get_table_path(table_name)
            return table_path.exists()
        except Exception:
            return False
    
    @contextmanager
    def _backup_table(self, table_name: str):
        """Context manager to create a backup before modifying a table."""
        if not self._table_exists(table_name):
            yield
            return
        
        table_path = self._get_table_path(table_name)
        backup_path = table_path.with_suffix(f'.bak_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
        
        try:
            # Create backup
            shutil.copy2(table_path, backup_path)
            logger.info(f"📁 Backup created: {backup_path.name}")
            yield
        except Exception as e:
            # Restore from backup if operation failed
            if backup_path.exists():
                shutil.copy2(backup_path, table_path)
                logger.warning(f"🔄 Restored from backup due to error: {e}")
            raise
        finally:
            # Clean up backup (keep only latest 5 backups per table)
            self._cleanup_backups(table_name)
    
    def _cleanup_backups(self, table_name: str, keep_count: int = 5):
        """Clean up old backup files, keeping only the most recent ones."""
        try:
            base_name = table_name.replace('.csv', '')
            backup_pattern = f"{base_name}.bak_*"
            backup_files = list(self._csv_directory.glob(backup_pattern))
            
            if len(backup_files) > keep_count:
                # Sort by modification time, keep newest
                backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                for old_backup in backup_files[keep_count:]:
                    old_backup.unlink()
                    logger.info(f"🗑️ Cleaned up old backup: {old_backup.name}")
        except Exception as e:
            logger.warning(f"⚠️ Backup cleanup failed: {e}")
    
    def _serialize_nested_data(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Serialize nested dictionaries and lists to JSON strings for CSV storage.
        
        Args:
            data: Dictionary or list of dictionaries to serialize
            
        Returns:
            Data with nested structures serialized to JSON strings
        """
        def serialize_value(value):
            if isinstance(value, (dict, list)):
                return json.dumps(value, ensure_ascii=False, separators=(',', ':'))
            return value
        
        if isinstance(data, list):
            return [
                {key: serialize_value(val) for key, val in row.items()}
                for row in data
            ]
        elif isinstance(data, dict):
            return {key: serialize_value(val) for key, val in data.items()}
        return data
    
    def _deserialize_nested_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Deserialize JSON strings back to nested dictionaries and lists.
        
        Args:
            data: List of dictionaries with JSON strings to deserialize
            
        Returns:
            Data with JSON strings deserialized back to nested structures
        """
        def deserialize_value(value):
            if isinstance(value, str):
                # Try to parse as JSON if it looks like JSON
                if (value.startswith('{') and value.endswith('}')) or \
                   (value.startswith('[') and value.endswith(']')):
                    try:
                        return json.loads(value)
                    except (json.JSONDecodeError, ValueError):
                        # If JSON parsing fails, return as string
                        pass
            return value
        
        return [
            {key: deserialize_value(val) for key, val in row.items()}
            for row in data
        ]
    
    def execute_query(self, table_name: str, conditions: Optional[Dict[str, Any]] = None, 
                     columns: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Execute a SELECT-like query on a CSV table.
        
        Args:
            table_name: Name of the CSV file (table)
            conditions: Dictionary of column:value pairs for filtering
            columns: List of columns to return (None for all columns)
            
        Returns:
            List of dictionaries representing query results
        """
        try:
            table_path = self._get_table_path(table_name)
            
            if not table_path.exists():
                logger.warning(f"⚠️ Table {table_name} does not exist")
                return []
            
            # Read CSV file
            df = pd.read_csv(table_path)
            
            # Apply conditions (WHERE clause equivalent)
            if conditions:
                for column, value in conditions.items():
                    if column in df.columns:
                        if isinstance(value, str) and '*' in value:
                            # Handle wildcard matching
                            pattern = value.replace('*', '.*')
                            df = df[df[column].astype(str).str.match(pattern, na=False)]
                        else:
                            df = df[df[column] == value]
            
            # Select specific columns if specified
            if columns:
                available_columns = [col for col in columns if col in df.columns]
                if available_columns:
                    df = df[available_columns]
            
            # Convert to list of dictionaries
            results = df.to_dict('records')
            
            # Deserialize nested JSON data back to dictionaries/lists
            results = self._deserialize_nested_data(results)
            
            logger.info(f"✅ Query executed on {table_name}, returned {len(results)} rows")
            return results
            
        except Exception as e:
            logger.error(f"❌ Query execution failed on {table_name}: {e}")
            raise
    
    def execute_insert(self, table_name: str, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> int:
        """
        Execute an INSERT-like operation on a CSV table.
        
        Args:
            table_name: Name of the CSV file (table)
            data: Dictionary or list of dictionaries to insert
            
        Returns:
            Number of rows inserted
        """
        try:
            table_path = self._get_table_path(table_name)
            
            # Ensure data is a list
            if isinstance(data, dict):
                data = [data]
            
            if not data:
                return 0
            
            # Serialize nested data for CSV storage
            serialized_data = self._serialize_nested_data(data)
            
            with self._backup_table(table_name):
                if table_path.exists():
                    # Read existing data
                    existing_df = pd.read_csv(table_path)
                    
                    # Create new dataframe from insert data
                    new_df = pd.DataFrame(serialized_data)
                    
                    # Ensure columns match (add missing columns with NaN)
                    for col in existing_df.columns:
                        if col not in new_df.columns:
                            new_df[col] = None
                    
                    for col in new_df.columns:
                        if col not in existing_df.columns:
                            existing_df[col] = None
                    
                    # Append new data
                    result_df = pd.concat([existing_df, new_df], ignore_index=True)
                else:
                    # Create new table
                    result_df = pd.DataFrame(serialized_data)
                
                # Write back to CSV
                result_df.to_csv(table_path, index=False)
                
                rows_inserted = len(data)
                logger.info(f"✅ INSERT executed on {table_name}, inserted {rows_inserted} rows")
                return rows_inserted
                
        except Exception as e:
            logger.error(f"❌ INSERT execution failed on {table_name}: {e}")
            raise
    
    def execute_update(self, table_name: str, data: Dict[str, Any], 
                      conditions: Optional[Dict[str, Any]] = None) -> int:
        """
        Execute an UPDATE-like operation on a CSV table.
        
        Args:
            table_name: Name of the CSV file (table)
            data: Dictionary of column:value pairs to update
            conditions: Dictionary of column:value pairs for filtering rows to update
            
        Returns:
            Number of rows affected
        """
        try:
            table_path = self._get_table_path(table_name)
            
            if not table_path.exists():
                logger.warning(f"⚠️ Table {table_name} does not exist")
                return 0
            
            with self._backup_table(table_name):
                # Read CSV file
                df = pd.read_csv(table_path)
                original_count = len(df)
                
                # Serialize nested data for CSV storage
                serialized_data = self._serialize_nested_data(data)
                
                # Create mask for rows to update
                mask = pd.Series([True] * len(df))
                
                if conditions:
                    for column, value in conditions.items():
                        if column in df.columns:
                            if isinstance(value, str) and '*' in value:
                                # Handle wildcard matching
                                pattern = value.replace('*', '.*')
                                mask &= df[column].astype(str).str.match(pattern, na=False)
                            else:
                                mask &= (df[column] == value)
                
                # Update matching rows
                affected_rows = mask.sum()
                for column, value in serialized_data.items():
                    df.loc[mask, column] = value
                
                # Write back to CSV
                df.to_csv(table_path, index=False)
                
                logger.info(f"✅ UPDATE executed on {table_name}, affected {affected_rows} rows")
                return affected_rows
                
        except Exception as e:
            logger.error(f"❌ UPDATE execution failed on {table_name}: {e}")
            raise
    
    def execute_delete(self, table_name: str, conditions: Optional[Dict[str, Any]] = None) -> int:
        """
        Execute a DELETE-like operation on a CSV table.
        
        Args:
            table_name: Name of the CSV file (table)
            conditions: Dictionary of column:value pairs for filtering rows to delete
            
        Returns:
            Number of rows affected
        """
        try:
            table_path = self._get_table_path(table_name)
            
            if not table_path.exists():
                logger.warning(f"⚠️ Table {table_name} does not exist")
                return 0
            
            with self._backup_table(table_name):
                # Read CSV file
                df = pd.read_csv(table_path)
                original_count = len(df)
                
                # Create mask for rows to keep (inverse of delete conditions)
                keep_mask = pd.Series([True] * len(df))
                
                if conditions:
                    for column, value in conditions.items():
                        if column in df.columns:
                            if isinstance(value, str) and '*' in value:
                                # Handle wildcard matching
                                pattern = value.replace('*', '.*')
                                keep_mask &= ~df[column].astype(str).str.match(pattern, na=False)
                            else:
                                keep_mask &= (df[column] != value)
                else:
                    # No conditions means delete all rows
                    keep_mask = pd.Series([False] * len(df))
                
                # Keep only non-matching rows
                df = df[keep_mask]
                affected_rows = original_count - len(df)
                
                # Write back to CSV
                df.to_csv(table_path, index=False)
                
                logger.info(f"✅ DELETE executed on {table_name}, affected {affected_rows} rows")
                return affected_rows
                
        except Exception as e:
            logger.error(f"❌ DELETE execution failed on {table_name}: {e}")
            raise
    
    def create_table(self, table_name: str, columns: List[str], data: Optional[List[Dict[str, Any]]] = None) -> bool:
        """
        Create a new CSV table with specified columns.
        
        Args:
            table_name: Name of the CSV file (table)
            columns: List of column names
            data: Optional initial data
            
        Returns:
            True if table was created successfully
        """
        try:
            table_path = self._get_table_path(table_name)
            
            if table_path.exists():
                logger.warning(f"⚠️ Table {table_name} already exists")
                return False
            
            # Create empty dataframe with specified columns
            df = pd.DataFrame(columns=columns)
            
            # Add initial data if provided
            if data:
                # Serialize nested data for CSV storage
                serialized_data = self._serialize_nested_data(data)
                df = pd.DataFrame(serialized_data, columns=columns)
            
            # Write to CSV
            df.to_csv(table_path, index=False)
            
            logger.info(f"✅ Table {table_name} created successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Table creation failed for {table_name}: {e}")
            raise
    
    def drop_table(self, table_name: str) -> bool:
        """
        Drop (delete) a CSV table.
        
        Args:
            table_name: Name of the CSV file (table)
            
        Returns:
            True if table was dropped successfully
        """
        try:
            table_path = self._get_table_path(table_name)
            
            if not table_path.exists():
                logger.warning(f"⚠️ Table {table_name} does not exist")
                return False
            
            # Create final backup before deletion
            backup_path = table_path.with_suffix(f'.deleted_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
            shutil.copy2(table_path, backup_path)
            
            # Delete the table
            table_path.unlink()
            
            logger.info(f"✅ Table {table_name} dropped successfully (backup: {backup_path.name})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Table drop failed for {table_name}: {e}")
            raise
    
    def list_tables(self) -> List[str]:
        """
        List all available tables (CSV files).
        
        Returns:
            List of table names
        """
        try:
            if not self._csv_directory:
                return []
            
            csv_files = list(self._csv_directory.glob("*.csv"))
            # Filter out backup files
            tables = [f.stem for f in csv_files if not any(x in f.name for x in ['.bak', '.deleted'])]
            
            logger.info(f"✅ Found {len(tables)} tables")
            return sorted(tables)
            
        except Exception as e:
            logger.error(f"❌ Failed to list tables: {e}")
            return []
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """
        Get information about a table (column names, row count, etc.).
        
        Args:
            table_name: Name of the CSV file (table)
            
        Returns:
            Dictionary with table information
        """
        try:
            table_path = self._get_table_path(table_name)
            
            if not table_path.exists():
                return {'exists': False}
            
            # Read CSV file
            df = pd.read_csv(table_path)
            
            info = {
                'exists': True,
                'path': str(table_path),
                'row_count': len(df),
                'column_count': len(df.columns),
                'columns': list(df.columns),
                'size_bytes': table_path.stat().st_size,
                'modified_time': datetime.fromtimestamp(table_path.stat().st_mtime).isoformat()
            }
            
            logger.info(f"✅ Table info retrieved for {table_name}")
            return info
            
        except Exception as e:
            logger.error(f"❌ Failed to get table info for {table_name}: {e}")
            raise
    
    def test_connection(self) -> bool:
        """
        Test the CSV database connection (directory access).
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            if not self._csv_directory:
                return False
            
            # Test by creating and removing a temporary file
            test_file = self._csv_directory / ".test_connection"
            test_file.touch()
            test_file.unlink()
            
            logger.info("✅ CSV database connection test successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ CSV database connection test failed: {e}")
            return False
    
    def get_directory_status(self) -> Dict[str, Any]:
        """
        Get CSV directory status and statistics.
        
        Returns:
            Dictionary with directory statistics
        """
        try:
            if not self._csv_directory:
                return {'accessible': False}
            
            tables = self.list_tables()
            csv_files = list(self._csv_directory.glob("*.csv"))
            backup_files = list(self._csv_directory.glob("*.bak*"))
            
            total_size = sum(f.stat().st_size for f in csv_files)
            
            return {
                'accessible': True,
                'directory': str(self._csv_directory.absolute()),
                'table_count': len(tables),
                'total_files': len(csv_files),
                'backup_files': len(backup_files),
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'tables': tables
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get directory status: {e}")
            return {'accessible': False, 'error': str(e)}


# Create singleton instance
db = CSVDatabase()


def get_db() -> CSVDatabase:
    """
    Get the CSV database singleton instance.
    
    Returns:
        CSVDatabase singleton instance
    """
    return db