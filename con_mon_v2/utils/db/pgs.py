"""
Database singleton for PostgreSQL operations in con_mon.

Provides a singleton pattern for database connections with connection pooling
and methods for executing SQL queries.
"""
import csv
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
import psycopg2
import psycopg2.pool
from contextlib import contextmanager
import logging
from con_mon_v2.utils.config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def datetime_handler(obj: Any) -> str:
    """Handle datetime serialization to string."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """Flatten nested dictionaries for CSV format."""
    items: list = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            # Serialize complex types to JSON strings
            if isinstance(v, (dict, list)):
                items.append((new_key, json.dumps(v, default=datetime_handler)))
            elif isinstance(v, datetime):
                items.append((new_key, v.isoformat()))
            else:
                items.append((new_key, v))
    return dict(items)


def unflatten_dict(flat_dict: Dict[str, Any], sep: str = '.') -> Dict[str, Any]:
    """Reconstruct nested dictionaries from flattened CSV format."""
    result = {}
    for key, value in flat_dict.items():
        if sep not in key:
            # Try to parse JSON strings back to objects
            if isinstance(value, str):
                try:
                    # Try to parse as JSON
                    parsed = json.loads(value)
                    result[key] = parsed
                except (json.JSONDecodeError, ValueError):
                    # Try to parse as datetime
                    try:
                        if 'T' in value and (':' in value or '+' in value):
                            result[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                        else:
                            result[key] = value
                    except ValueError:
                        result[key] = value
            else:
                result[key] = value
        else:
            # Nested key - reconstruct hierarchy
            keys = key.split(sep)
            current = result
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]
            
            # Handle the final value
            final_key = keys[-1]
            if isinstance(value, str):
                try:
                    current[final_key] = json.loads(value)
                except (json.JSONDecodeError, ValueError):
                    try:
                        if 'T' in value and (':' in value or '+' in value):
                            current[final_key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                        else:
                            current[final_key] = value
                    except ValueError:
                        current[final_key] = value
            else:
                current[final_key] = value
    
    return result


class PostgreSQLDatabase:
    """
    Singleton class for PostgreSQL database operations.
    
    Manages connection pooling and provides methods for executing SQL queries.
    """
    
    _instance: Optional['PostgreSQLDatabase'] = None
    _connection_pool: Optional[psycopg2.pool.SimpleConnectionPool] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'PostgreSQLDatabase':
        if cls._instance is None:
            cls._instance = super(PostgreSQLDatabase, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._initialized = True
            self._setup_connection_pool()
    
    def _setup_connection_pool(self):
        """Initialize the connection pool with database configuration."""
        try:
            # Database configuration from environment variables
            db_config = {
                'host': settings.DB_HOST,
                'port': settings.DB_PORT,
                'database': settings.DB_NAME,
                'user': settings.DB_USER,
                'password': settings.DB_PASSWORD,
            }
            
            # Create connection pool
            self._connection_pool = psycopg2.pool.SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                **db_config
            )
            
            logger.info(f"✅ Database connection pool created for {db_config['host']}:{db_config['port']}/{db_config['database']}")
            
        except psycopg2.Error as e:
            logger.warning(f"⚠️ Database connection pool creation failed: {e}")
            logger.info("💡 Database operations will be unavailable until connection is established")
            self._connection_pool = None
        except Exception as e:
            logger.warning(f"⚠️ Unexpected error creating connection pool: {e}")
            logger.info("💡 Database operations will be unavailable until connection is established")
            self._connection_pool = None
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for getting a database connection from the pool.
        
        Yields:
            psycopg2.connection: Database connection
            
        Example:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM table")
        """
        if not self._connection_pool:
            raise Exception("Database connection pool not initialized")
        
        connection = None
        try:
            connection = self._connection_pool.getconn()
            yield connection
        except psycopg2.Error as e:
            if connection:
                connection.rollback()
            logger.error(f"❌ Database operation failed: {e}")
            raise
        finally:
            if connection:
                self._connection_pool.putconn(connection)
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """
        Execute a SELECT query and return results as list of dictionaries.
        
        Args:
            query: SQL query string
            params: Query parameters (optional)
            
        Returns:
            List of dictionaries representing query results
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                
                # Get column names
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                
                # Fetch results and convert to dictionaries
                results = []
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))
                
                logger.info(f"✅ Query executed successfully, returned {len(results)} rows")
                return results
    
    def execute_insert(self, query: str, params: Optional[tuple] = None) -> Optional[int]:
        """
        Execute an INSERT query and return the inserted row ID.
        
        Args:
            query: SQL INSERT query string
            params: Query parameters (optional)
            
        Returns:
            Inserted row ID if available, None otherwise
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                
                # Try to get the inserted row ID
                row_id = None
                if cursor.description:
                    row = cursor.fetchone()
                    if row:
                        row_id = row[0]
                
                conn.commit()
                logger.info(f"✅ INSERT executed successfully, row ID: {row_id}")
                return row_id
    
    def execute_update(self, query: str, params: Optional[tuple] = None) -> int:
        """
        Execute an UPDATE query and return the number of affected rows.
        
        Args:
            query: SQL UPDATE query string
            params: Query parameters (optional)
            
        Returns:
            Number of affected rows
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                affected_rows = cursor.rowcount
                conn.commit()
                logger.info(f"✅ UPDATE executed successfully, affected {affected_rows} rows")
                return affected_rows
    
    def execute_delete(self, query: str, params: Optional[tuple] = None) -> int:
        """
        Execute a DELETE query and return the number of affected rows.
        
        Args:
            query: SQL DELETE query string
            params: Query parameters (optional)
            
        Returns:
            Number of affected rows
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                affected_rows = cursor.rowcount
                conn.commit()
                logger.info(f"✅ DELETE executed successfully, affected {affected_rows} rows")
                return affected_rows
    
    def execute_script(self, script: str) -> None:
        """
        Execute a SQL script (multiple statements).
        
        Args:
            script: SQL script string with multiple statements
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(script)
                conn.commit()
                logger.info("✅ SQL script executed successfully")
    
    def test_connection(self) -> bool:
        """
        Test the database connection.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    if result and result[0] == 1:
                        logger.info("✅ Database connection test successful")
                        return True
            return False
        except Exception as e:
            logger.error(f"❌ Database connection test failed: {e}")
            return False
    
    def close_pool(self):
        """Close all connections in the pool."""
        if self._connection_pool:
            self._connection_pool.closeall()
            logger.info("✅ Database connection pool closed")
    
    def get_pool_status(self) -> Dict[str, int]:
        """
        Get connection pool status.
        
        Returns:
            Dictionary with pool statistics
        """
        if not self._connection_pool:
            return {'total': 0, 'available': 0, 'used': 0}
        
        return {
            'total': self._connection_pool.maxconn,
            'available': len(self._connection_pool._pool),
            'used': self._connection_pool.maxconn - len(self._connection_pool._pool)
        }

    def export_table_to_csv(
        self,
        table_name: str,
        output_path: Optional[str] = None,
        where_clause: Optional[str] = None
    ) -> str:
        """
        Export a PostgreSQL table to CSV format.

        Args:
            table_name: Name of the table to export
            output_path: Output CSV file path (defaults to data/csv/{table_name}.csv)
            where_clause: Optional WHERE clause to filter data (e.g., "is_deleted = false")
            flatten_jsonb: Whether to flatten JSONB fields for CSV compatibility

        Returns:
            Path to the created CSV file

        Raises:
            Exception: If export fails
        """
        try:
            # Set default output path
            if output_path is None:
                csv_dir = Path("data/csv")
                csv_dir.mkdir(parents=True, exist_ok=True)
                output_path = csv_dir / f"{table_name}.csv"
            else:
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)

            # Build query
            query = f"SELECT * FROM {table_name}"
            if where_clause:
                query += f" WHERE {where_clause}"
            query += " ORDER BY id"

            logger.info(f"🔄 Exporting table '{table_name}' to CSV...")
            logger.info(f"   • Query: {query}")
            logger.info(f"   • Output: {output_path}")

            # Execute query
            data = self.execute_query(query)

            if not data:
                logger.warning(f"⚠️ No data found in table '{table_name}'")
                return str(output_path)

            # Process data for CSV export
            processed_data = []
            for row in data:
                if flatten_jsonb:
                    # Flatten nested dictionaries (JSONB fields)
                    flattened_row = flatten_dict(row)
                    processed_data.append(flattened_row)
                else:
                    # Keep original structure, just serialize complex types
                    serialized_row = {}
                    for key, value in row.items():
                        if isinstance(value, (dict, list)):
                            serialized_row[key] = json.dumps(value, default=datetime_handler)
                        elif isinstance(value, datetime):
                            serialized_row[key] = value.isoformat()
                        else:
                            serialized_row[key] = value
                    processed_data.append(serialized_row)

            # Get field names from first row
            fieldnames = list(processed_data[0].keys()) if processed_data else []

            # Write to CSV
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(processed_data)

            logger.info(f"✅ Exported {len(processed_data)} rows from '{table_name}' to {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"❌ Failed to export table '{table_name}': {e}")
            raise

    def import_csv_to_table(
        self,
        table_name: str,
        csv_path: str,
        update_existing: bool = True,
        batch_size: int = 100
    ) -> int:
        """
        Import CSV data to a PostgreSQL table.

        Args:
            table_name: Name of the target table
            csv_path: Path to the CSV file to import
            update_existing: Whether to update existing records (based on ID)
            unflatten_jsonb: Whether to reconstruct JSONB fields from flattened CSV
            batch_size: Number of records to process in each batch

        Returns:
            Number of records imported/updated

        Raises:
            Exception: If import fails
        """
        try:
            csv_path = Path(csv_path)
            if not csv_path.exists():
                raise FileNotFoundError(f"CSV file not found: {csv_path}")

            logger.info(f"🔄 Importing CSV data to table '{table_name}'...")
            logger.info(f"   • Source: {csv_path}")
            logger.info(f"   • Update existing: {update_existing}")
            logger.info(f"   • Unflatten JSONB: {unflatten_jsonb}")

            # Read CSV data
            df = pd.read_csv(csv_path)

            if df.empty:
                logger.warning(f"⚠️ CSV file is empty: {csv_path}")
                return 0

            # Convert DataFrame to list of dictionaries
            csv_data = df.to_dict('records')

            # Process data for database import
            processed_data = []
            for row in csv_data:
                # Handle NaN values
                processed_row = {k: (None if pd.isna(v) else v) for k, v in row.items()}

                if unflatten_jsonb:
                    # Reconstruct nested dictionaries from flattened fields
                    processed_row = unflatten_dict(processed_row)
                else:
                    # Try to parse JSON strings back to objects
                    for key, value in processed_row.items():
                        if isinstance(value, str) and value.startswith('{'):
                            try:
                                processed_row[key] = json.loads(value)
                            except json.JSONDecodeError:
                                pass  # Keep as string if not valid JSON

                processed_data.append(processed_row)

            # Get table schema to build proper INSERT/UPDATE queries
            schema_query = """
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = %s 
                ORDER BY ordinal_position
            """
            schema = self.execute_query(schema_query, (table_name,))

            if not schema:
                raise Exception(f"Table '{table_name}' not found or no access")

            column_names = [col['column_name'] for col in schema]

            # Process in batches
            total_processed = 0

            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    for i in range(0, len(processed_data), batch_size):
                        batch = processed_data[i:i + batch_size]

                        for row in batch:
                            # Filter row to only include columns that exist in the table
                            filtered_row = {k: v for k, v in row.items() if k in column_names}

                            if not filtered_row:
                                continue

                            # Build INSERT or UPDATE query
                            if update_existing and 'id' in filtered_row:
                                # UPDATE existing record
                                set_clause = ', '.join([f"{k} = %s" for k in filtered_row.keys() if k != 'id'])
                                if set_clause:
                                    update_query = f"""
                                        UPDATE {table_name} 
                                        SET {set_clause}
                                        WHERE id = %s
                                    """
                                    values = [v for k, v in filtered_row.items() if k != 'id']
                                    values.append(filtered_row['id'])

                                    cursor.execute(update_query, values)
                                    if cursor.rowcount == 0:
                                        # Record doesn't exist, INSERT it
                                        columns = ', '.join(filtered_row.keys())
                                        placeholders = ', '.join(['%s'] * len(filtered_row))
                                        insert_query = f"""
                                            INSERT INTO {table_name} ({columns})
                                            VALUES ({placeholders})
                                        """
                                        cursor.execute(insert_query, list(filtered_row.values()))
                            else:
                                # INSERT new record
                                columns = ', '.join(filtered_row.keys())
                                placeholders = ', '.join(['%s'] * len(filtered_row))
                                insert_query = f"""
                                    INSERT INTO {table_name} ({columns})
                                    VALUES ({placeholders})
                                    ON CONFLICT (id) DO NOTHING
                                """
                                cursor.execute(insert_query, list(filtered_row.values()))

                            total_processed += 1

                        # Commit batch
                        conn.commit()
                        logger.info(f"   • Processed batch {i // batch_size + 1}: {len(batch)} records")

            logger.info(f"✅ Imported {total_processed} records to '{table_name}'")
            return total_processed

        except Exception as e:
            logger.error(f"❌ Failed to import CSV to table '{table_name}': {e}")
            raise


# Create singleton instance
db = PostgreSQLDatabase()


def get_db() -> PostgreSQLDatabase:
    """
    Get the database singleton instance.
    
    Returns:
        PostgreSQLDatabase singleton instance
    """
    return db 