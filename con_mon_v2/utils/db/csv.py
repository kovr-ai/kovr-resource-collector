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
from con_mon_v2.utils.config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from con_mon_v2.utils.db.base import SQLDatabase as _BaseSQLDatabase  # for interface parity only


class CSVDatabase(_BaseSQLDatabase):
    """
    Singleton class for CSV file database operations.
    
    Manages CRUD operations on CSV files where each file represents a table.
    Files are stored in data/csv/ directory.
    
    Now supports both SQL query strings (like PostgreSQL) and structured queries.
    """
    class SQLParser(_BaseSQLDatabase.SQLParser):
        """Build structured query objects for CSV backend (no SQL strings).

        Returns dict payloads consumable by `execute_query`, following the
        same constructor interface as the base parser: table_name, select,
        update, where. Operations set `op` to one of: select|insert|update|delete.
        """

        def __init__(
            self,
            table_name: str,
            select: list | None = None,
            update: dict | None = None,
            where: dict | None = None,
        ):
            self.table_name = table_name
            self.select = select
            self.update = update
            self.where = where

        def _build_where(self) -> Dict[str, Any]:
            return dict(self.where) if self.where else {}

        @property
        def select_query(self) -> Dict[str, Any]:
            return {
                'op': 'select',
                'table_name': self.table_name,
                'select': list(self.select) if self.select else None,
                'where': self._build_where(),
            }

        @property
        def insert_query(self) -> Dict[str, Any]:
            return {
                'op': 'insert',
                'table_name': self.table_name,
                'values': dict(self.update or {}),
            }

        @property
        def insert_params(self) -> list:
            return []

        @property
        def update_query(self) -> Dict[str, Any]:
            if not self.update:
                raise ValueError("Update operation requires a non-empty `update` mapping")
            return {
                'op': 'update',
                'table_name': self.table_name,
                'values': dict(self.update),
                'where': self._build_where(),
            }

        @property
        def delete_query(self) -> Dict[str, Any]:
            if not self.where:
                raise ValueError("Refusing to build DELETE without a WHERE clause")
            return {
                'op': 'delete',
                'table_name': self.table_name,
                'where': self._build_where(),
            }

        @property
        def delete_params(self) -> list:
            return []

    # CONFIG PROPERTIES
    @property
    def _db_config(self) -> Dict[str, Any]:
        # Mirror base contract; CSV uses directory path instead of network params
        return {
            'csv_data': settings.CSV_DATA,
            'minconn': 1,
            'maxconn': 1,
        }

    @property
    def _db_class(self) -> Any:  # type: ignore[name-defined]
        # Provide a minimal pool that satisfies getconn/putconn/closeall used by base
        class SimpleCSVConnection:
            def cursor(self):
                class _NoopCursor:
                    description = []
                    def __enter__(self):
                        return self
                    def __exit__(self, exc_type, exc, tb):
                        return False
                    def execute(self, *args, **kwargs):
                        return None
                    def fetchone(self):
                        return None
                    def fetchall(self):
                        return []
                return _NoopCursor()

            def commit(self):
                return None

            def rollback(self):
                return None

        class SimpleCSVConnectionPool:
            def __init__(self, csv_data: Optional[str] = None, minconn: int = 1, maxconn: int = 1, **kwargs):
                self.csv_data = csv_data
                self.minconn = minconn
                self.maxconn = maxconn
                self._pool = [SimpleCSVConnection()]
                self._closed = False

            def getconn(self):
                return self._pool[0]

            def putconn(self, conn):
                return None

            def closeall(self):
                self._closed = True

        return SimpleCSVConnectionPool

    def close_connection(self):
        """Close the CSV pseudo-connection pool."""
        if getattr(self, "_connection", None):
            self._connection.closeall()
            logger.info("✅ CSV connection pool closed")

    def get_status(self) -> Dict[str, int]:
        """Return pseudo-pool statistics."""
        pool = getattr(self, "_connection", None)
        if not pool:
            return {'total': 0, 'available': 0, 'used': 0}
        try:
            return {
                'total': 1,
                'available': 1,
                'used': 0,
            }
        except Exception:
            return {'total': 0, 'available': 0, 'used': 0}
    
    def _setup_csv_directory(self):
        """Initialize the CSV directory path and ensure it exists."""
        try:
            # Set up CSV directory path
            self._csv_directory = Path(settings.CSV_DATA)
            
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
        return self._csv_directory / f"{table_name}.csv"
    
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
    
    def _is_json_field(self, field_name: str) -> bool:
        """Check if a field should be parsed as JSON."""
        # Known JSON field patterns
        json_fields = {
            'metadata.tags',
            'fix_details.instructions',
            'metadata.operation.logic',
        }
        
        # Field name patterns that typically contain JSON
        json_patterns = [
            '.tags', '.instructions', 'metadata', 'config', 'settings', 
            'data', 'profile', 'user', 'employee', 'preferences', 'features',
            'audit', 'validation', 'permissions'
        ]
        
        # Check exact matches first
        if field_name in json_fields:
            return True
            
        # Check if field name contains JSON patterns
        for pattern in json_patterns:
            if pattern in field_name.lower():
                return True
                
        return False
    
    def _deserialize_nested_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Deserialize nested JSON data from CSV format.
        
        The CSV stores nested data in flattened format with dot notation:
        - output_statements.failure -> {"output_statements": {"failure": "..."}}
        - metadata.tags -> {"metadata": {"tags": [...]}}
        
        Args:
            data: List of flat dictionaries from CSV
            
        Returns:
            List of dictionaries with proper nested structure
        """
        result = []
        
        for row in data:
            nested_row = {}
            
            for key, value in row.items():
                # Handle pandas NaN values first
                if pd.isna(value):
                    value = None
                
                # Convert ID to string only for Check model compatibility, not for tests
                # Only do this for the main checks table
                if key == 'id' and isinstance(value, (int, float)):
                    # Keep as int for test compatibility, only convert to string for checks table
                    if hasattr(self, '_current_table') and self._current_table == 'checks':
                        value = str(int(value))
                    else:
                        value = int(value)  # Ensure it's an int, not float
                
                # Parse JSON strings for fields that might contain JSON
                if isinstance(value, str) and value.strip():
                    # Try to detect JSON by looking for JSON-like patterns
                    if ((value.startswith('{') and value.endswith('}')) or 
                        (value.startswith('[') and value.endswith(']')) or
                        self._is_json_field(key)):
                        try:
                            parsed_value = json.loads(value)
                            value = parsed_value
                        except (json.JSONDecodeError, TypeError):
                            # If JSON parsing fails, keep as string
                            pass
                
                # Handle dot notation for nested fields
                if '.' in key:
                    self._set_nested_value(nested_row, key, value)
                else:
                    nested_row[key] = value
            
            result.append(nested_row)
        
        return result
    
    def _set_nested_value(self, obj: Dict[str, Any], key_path: str, value: Any):
        """
        Set a nested value using dot notation.
        
        Args:
            obj: Dictionary to set value in
            key_path: Dot-separated key path (e.g., 'metadata.tags')
            value: Value to set
        """
        keys = key_path.split('.')
        current = obj
        
        # Navigate to the parent object, creating nested dicts as needed
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set the final value
        final_key = keys[-1]
        current[final_key] = value
    
    def execute_query(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Execute a structured query object (output of SQLParser) on CSV.

        Expected query shape:
            {
                'op': 'select'|'insert'|'update'|'delete',
                'table_name': str,
                'select': Optional[List[str]],   # for select
                'values': Optional[Dict[str, Any]],  # for insert/update
                'where': Optional[Dict[str, Any]],
            }

        Returns list of dict rows, mirroring PostgreSQL RETURNING * behavior for
        insert/update/delete. Delete returns the rows that were removed.
        """
        try:
            if not isinstance(query, dict):
                raise ValueError("CSVDatabase.execute_query expects a structured dict from SQLParser")

            op = query.get('op', 'select')
            table_name = query.get('table_name')
            if not table_name:
                raise ValueError("query.table_name is required")

            where: Optional[Dict[str, Any]] = query.get('where') or None
            select_cols: Optional[List[str]] = query.get('select') or None

            if op == 'select':
                return self._execute_structured_query(table_name, conditions=where, columns=select_cols)

            if op == 'insert':
                values: Dict[str, Any] = query.get('values') or {}
                # Perform insert
                self.execute_insert(table_name, values)
                # Try to return the inserted rows
                if where:
                    # If caller provided where, combine with inserted values for precision
                    combined_where = dict(where)
                    for k, v in values.items():
                        combined_where.setdefault(k, v)
                    return self._execute_structured_query(table_name, conditions=combined_where)
                if 'id' in values:
                    return self._execute_structured_query(table_name, conditions={'id': values['id']})
                # Fallback: return the inserted payload
                return [values]

            if op == 'update':
                values: Dict[str, Any] = query.get('values') or {}
                # Apply update
                self.execute_update(table_name, data=values, conditions=where)
                # Return updated rows (post-update state)
                return self._execute_structured_query(table_name, conditions=where)

            if op == 'delete':
                # Capture rows before deletion to return them
                rows_to_delete = self._execute_structured_query(table_name, conditions=where)
                self.execute_delete(table_name, conditions=where)
                return rows_to_delete

            raise ValueError(f"Unsupported operation: {op}")
            
        except Exception as e:
            logger.error(f"❌ Query execution failed: {e}")
            return []

    def execute_select(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Execute a simple SELECT ... FROM <table> [WHERE ...] by parsing minimal pieces.

        For CSV backend, we expect basic patterns used by data loaders. This translates
        the SQL to a structured call to `_execute_structured_query`.
        """
        try:
            query = (query or '').strip().rstrip(';')
            # Very simple parse: SELECT <cols> FROM <table> [WHERE ...] [ORDER BY id]
            import re as _re
            m = _re.match(r"SELECT\s+(.*?)\s+FROM\s+(\w+)(?:\s+WHERE\s+(.*?))?(?:\s+ORDER\s+BY\s+(.*))?$",
                          query, _re.IGNORECASE)
            if not m:
                return []
            cols_str, table, where_clause, order_by = m.groups()
            columns = None if cols_str.strip() == '*' else [c.strip() for c in cols_str.split(',')]
            conditions: Dict[str, Any] = {}
            if where_clause:
                # Support simple equality-only conditions joined by AND
                for part in where_clause.split(' AND '):
                    if '=' in part:
                        k, v = part.split('=', 1)
                        conditions[k.strip()] = v.strip().strip("'\"")
            return self._execute_structured_query(table, conditions or None, columns, order_by)
        except Exception as e:
            logger.error(f"❌ SELECT execution failed: {e}")
            return []
    
    def _execute_structured_query(self, table_name: str, conditions: Optional[Dict[str, Any]] = None, 
                                 columns: Optional[List[str]] = None, order_by: Optional[str] = None) -> List[Dict[str, Any]]:
        """Execute a structured query (original CSV database interface)."""
        try:
            # Set current table context for ID conversion logic
            self._current_table = table_name
            
            table_path = self._get_table_path(table_name)
            
            if not table_path.exists():
                logger.warning(f"⚠️ Table {table_name} does not exist")
                return []
            
            # Read CSV file
            df = pd.read_csv(table_path)
            
            # Handle column selection for nested fields
            if columns:
                # Expand nested field names to their flattened equivalents
                expanded_columns = self._expand_nested_columns(columns, df.columns)
                available_columns = [col for col in expanded_columns if col in df.columns]
                
                if available_columns:
                    df = df[available_columns]
                else:
                    logger.warning(f"⚠️ None of the requested columns {columns} found in table {table_name}")
                    # If no columns found, return empty results
                    return []
            
            # Apply conditions (WHERE clause equivalent)
            if conditions:
                for column, value in conditions.items():
                    if column in df.columns:
                        if isinstance(value, list):
                            # Handle IN clause
                            df = df[df[column].isin(value)]
                        elif isinstance(value, str) and '*' in value:
                            # Handle wildcard matching
                            pattern = value.replace('*', '.*')
                            df = df[df[column].astype(str).str.match(pattern, na=False)]
                        else:
                            # Handle equality
                            df = df[df[column] == value]
            
            # Apply ORDER BY
            if order_by:
                # Simple ORDER BY support (column name only)
                order_column = order_by.replace('DESC', '').replace('ASC', '').strip()
                ascending = 'DESC' not in order_by.upper()
                if order_column in df.columns:
                    df = df.sort_values(by=order_column, ascending=ascending)
            
            # Convert to list of dictionaries
            results = df.to_dict('records')
            
            # Deserialize nested JSON data back to dictionaries/lists
            results = self._deserialize_nested_data(results)
            
            logger.info(f"✅ Query executed on {table_name}, returned {len(results)} rows")
            return results
            
        except Exception as e:
            logger.error(f"❌ Structured query execution failed on {table_name}: {e}")
            return []
        finally:
            # Clean up table context
            if hasattr(self, '_current_table'):
                delattr(self, '_current_table')
    
    def _expand_nested_columns(self, requested_columns: List[str], available_columns: List[str]) -> List[str]:
        """
        Expand nested column names to their flattened equivalents.
        
        For example:
        - 'output_statements' -> ['output_statements.failure', 'output_statements.partial', 'output_statements.success']
        - 'metadata' -> ['metadata.tags', 'metadata.category', 'metadata.severity', ...]
        
        Args:
            requested_columns: List of column names requested (may include nested fields)
            available_columns: List of actual columns in the CSV
            
        Returns:
            List of expanded column names that exist in the CSV
        """
        expanded = []
        
        for col in requested_columns:
            if col in available_columns:
                # Direct column exists, use it
                expanded.append(col)
            else:
                # Look for flattened versions of this column
                matching_columns = [
                    csv_col for csv_col in available_columns 
                    if csv_col.startswith(f"{col}.")
                ]
                if matching_columns:
                    expanded.extend(matching_columns)
                else:
                    # Column not found in any form, keep original for error reporting
                    expanded.append(col)
        
        return expanded
    
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