"""
Database singleton for PostgreSQL operations in con_mon.

Implements a PostgreSQL-backed database by extending the shared
`SQLDatabase` base so all CRUD operations and pooling behavior are
standardized across backends. Keeps backward-compatible helpers and
API surface (e.g., `_connection_pool`, `close_pool`, `get_pool_status`).
"""
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
import psycopg2
import psycopg2.pool
import logging
from con_mon.utils.db.base import SQLDatabase
from con_mon.utils.config import settings

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


class PostgreSQLDatabase(SQLDatabase):
    """
    PostgreSQL implementation of the shared SQL database interface.
    """
    class SQLParser(SQLDatabase.SQLParser):
        """Build PostgreSQL SQL statements from structured inputs.

        Properties return (sql, params) tuples suitable for execute_* methods.
        """

        def _build_where_clause(self) -> tuple[str, list]:
            """Construct a WHERE clause and its parameters.

            Returns:
                A tuple of (where_sql, params). If no filters provided, returns ('', []).
            """
            if not self.where:
                return "", []

            clauses: list[str] = []
            params: list = []

            for column_name, value in self.where.items():
                if value is None:
                    clauses.append(f"{column_name} IS NULL")
                elif isinstance(value, (list, tuple)):
                    if len(value) == 0:
                        # Empty IN set should never match; use a false predicate
                        clauses.append("1 = 0")
                    else:
                        placeholders = ", ".join(["%s"] * len(value))
                        clauses.append(f"{column_name} IN ({placeholders})")
                        params.extend(list(value))
                else:
                    clauses.append(f"{column_name} = %s")
                    params.append(value)

            where_sql = " WHERE " + " AND ".join(clauses) if clauses else ""
            return where_sql, params

        @property
        def select_query(self) -> tuple[str, tuple | None]:
            columns = '*'
            if self.select:
                columns = ", ".join(self.select)
            base = f"SELECT {columns} FROM {self.table_name}"
            where_sql, where_params = self._build_where_clause()
            sql = base + where_sql
            params = tuple(where_params) if where_params else None
            return sql, params

        @property
        def insert_query(self) -> tuple[str, tuple | None]:
            """Build an INSERT statement with placeholders.

            Uses `update` as the source of column->value mappings.
            Returns the SQL string (RETURNING * for convenience).
            """
            # Empty or missing values -> DEFAULT VALUES
            if not self.update:
                return (f"INSERT INTO {self.table_name} DEFAULT VALUES RETURNING *", None)

            # Ensure deterministic column order
            column_names = list(self.update.keys())
            placeholders = ", ".join(["%s"] * len(column_names))
            columns_sql = ", ".join(column_names)
            sql = (
                f"INSERT INTO {self.table_name} ({columns_sql}) "
                f"VALUES ({placeholders}) RETURNING *"
            )
            params = tuple(self.update[k] for k in self.update.keys())
            return sql, params

        @property
        def update_query(self) -> tuple[str, tuple | None]:
            """Build an UPDATE statement with placeholders.

            Requires `update` to be non-empty. `where` is optional but
            recommended; if omitted, the statement updates all rows.
            Returns the SQL string (RETURNING * for convenience).
            """
            if not self.update:
                raise ValueError("Update operation requires a non-empty `update` mapping")

            set_clause = ", ".join([f"{col} = %s" for col in self.update.keys()])
            where_sql, where_params = self._build_where_clause()
            sql = f"UPDATE {self.table_name} SET {set_clause}{where_sql} RETURNING *"
            params = tuple(self.update[k] for k in self.update.keys())
            if where_params:
                params = params + tuple(where_params)
            return sql, params

        @property
        def delete_query(self) -> tuple[str, tuple | None]:
            """Build a DELETE statement with placeholders.

            For safety, requires a non-empty `where` clause; otherwise raises.
            Returns the SQL string (RETURNING * for convenience).
            """
            if not self.where:
                raise ValueError("Refusing to build DELETE without a WHERE clause")
            where_sql, where_params = self._build_where_clause()
            sql = f"DELETE FROM {self.table_name}{where_sql} RETURNING *"
            params = tuple(where_params) if where_params else None
            return sql, params

    # CONFIG PROPERTIES
    @property
    def _db_config(self) -> Dict[str, Any]:
        return {
            'minconn': 1,
            'maxconn': 10,
            'host': settings.DB_HOST,
            'port': settings.DB_PORT,
            'database': settings.DB_NAME,
            'user': settings.DB_USER,
            'password': settings.DB_PASSWORD,
        }

    # CONFIG PROPERTIES
    @property
    def _db_class(self) -> Any:
        return psycopg2.pool.SimpleConnectionPool

    def close_connection(self):
        """Close all connections in the pool."""
        if getattr(self, "_connection", None):
            # psycopg2 SimpleConnectionPool supports closeall
            self._connection.closeall()
            logger.info("✅ Database connection pool closed")

    def get_status(self) -> Dict[str, int]:
        """Return pool statistics in a standardized format."""
        if not self._connection:
            return {'total': 0, 'available': 0, 'used': 0}
        try:
            return {
                'total': self._connection.maxconn,
                'available': len(self._connection._pool),
                'used': self._connection.maxconn - len(self._connection._pool)
            }
        except Exception:
            # Fallback if internals differ
            return {'total': 0, 'available': 0, 'used': 0}

    # Backward-compatible helpers
    def close_pool(self):
        self.close_connection()

    def get_pool_status(self) -> Dict[str, int]:
        return self.get_status()

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

    def export_table_to_csv(
        self,
        table_name: str,
        where_clause: Optional[str] = None
    ) -> str:
        """
        Export a PostgreSQL table to CSV format.

        Args:
            table_name: Name of the table to export
            where_clause: Optional WHERE clause to filter data (e.g., "is_deleted = false")

        Returns:
            Path to the created CSV file

        Raises:
            Exception: If export fails
        """
        # Build query
        query = f"SELECT * FROM {table_name}"
        if where_clause:
            query += f" WHERE {where_clause}"
        query += " ORDER BY id"

        logger.info(f"🔄 Exporting table '{table_name}' to CSV...")
        logger.info(f"   • Query: {query}")

        # Execute query
        data = self.execute('select', table_name=table_name)

        # Use CSVDatabase to write the data
        from .csv import get_db as get_csv_db
        csv_db = get_csv_db()

        if not data:
            logger.warning(f"⚠️ No data found in table '{table_name}'")
            csv_db.execute('insert', table_name=table_name, update={})
            return str(csv_db._get_table_path(table_name))

        # Write to CSV
        rows_inserted = csv_db.execute('insert', table_name=table_name, update=data)
        
        csv_path = csv_db._get_table_path(table_name)
        logger.info(f"✅ Exported {rows_inserted} rows from '{table_name}' to {csv_path}")
        return str(csv_path)

    def import_csv_to_table(
        self,
        table_name: str,
        update_existing: bool = True,
        batch_size: int = 100
    ) -> int:
        """
        Import CSV data to a PostgreSQL table.

        Args:
            table_name: Name of the target table
            update_existing: Whether to update existing records (based on ID)
            batch_size: Number of records to process in each batch

        Returns:
            Number of records imported/updated

        Raises:
            Exception: If import fails
        """
        # Use CSVDatabase to read the data
        from .csv import get_db as get_csv_db
        csv_db = get_csv_db()
        
        logger.info(f"🔄 Importing CSV data to table '{table_name}'...")
        csv_path = csv_db._get_table_path(table_name)
        logger.info(f"   • Source: {csv_path}")
        logger.info(f"   • Update existing: {update_existing}")

        # Read CSV data
        query = f"SELECT * FROM {table_name}"
        csv_data = csv_db.execute('select', table_name=table_name)

        if not csv_data:
            logger.warning(f"⚠️ CSV file is empty or not found: {csv_path}")
            return 0

        logger.info(f"   • Read {len(csv_data)} rows from CSV")

        # Get table schema to build proper INSERT/UPDATE queries
        schema_query = """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = %s 
            ORDER BY ordinal_position
        """
        schema = self.execute_select(schema_query, (table_name,))

        if not schema:
            raise Exception(f"Table '{table_name}' not found or no access")

        column_names = [col['column_name'] for col in schema]

        # Process in batches
        total_processed = 0

        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                for i in range(0, len(csv_data), batch_size):
                    batch = csv_data[i:i + batch_size]

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

    # DML helpers (explicit)
    def execute_insert(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Execute INSERT and return rows from RETURNING if present; commit transaction."""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                conn.commit()
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                if columns:
                    return [dict(zip(columns, row)) for row in cursor.fetchall()]
                return []

    def execute_update(self, query: str, params: Optional[tuple] = None) -> int:
        """Execute UPDATE and return affected row count; commit transaction."""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                affected = cursor.rowcount
                conn.commit()
                return affected

    def execute_delete(self, query: str, params: Optional[tuple] = None) -> int:
        """Execute DELETE and return affected row count; commit transaction."""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                affected = cursor.rowcount
                conn.commit()
                return affected

    def execute_select(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Execute SELECT and return list of dict rows (no commit)."""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                return [dict(zip(columns, row)) for row in cursor.fetchall()]


def get_db() -> PostgreSQLDatabase:
    """
    Get the database singleton instance.
    
    Returns:
        PostgreSQLDatabase singleton instance
    """
    return PostgreSQLDatabase()