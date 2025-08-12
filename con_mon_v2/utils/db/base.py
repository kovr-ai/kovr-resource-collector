"""
Database singleton for SQL operations in con_mon.

Provides a singleton pattern for database connections
and methods for executing SQL queries.
"""
import logging
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from con_mon_v2.utils.config import settings
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SQLDatabase:
    class ConnectionError(Exception):
        pass
    """
    Singleton class for SQL database operations.

    Manages connection and provides methods for executing SQL queries.
    """

    _instance: Optional['SQLDatabase'] = None
    _connection: Optional[Any] = None
    _initialized: bool = False

    def __new__(cls) -> 'SQLDatabase':
        if cls._instance is None:
            cls._instance = super(SQLDatabase, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._initialized = True
            self._setup_connection()

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

    @property
    def _db_class(self) -> Any:
        # return psycopg2.pool.SimpleConnectionPool
        raise NotImplementedError()

    # CONNECTION OPERATIONS
    def _setup_connection(self):
        """Initialize the connection with database configuration."""
        try:
            # Create connection
            self._connection = self._db_class(
                **self._db_config
            )

            logger.info(f"✅ Database connection created for {self._db_config['host']}:{self._db_config['port']}/{self._db_config['database']}")

        except self.ConnectionError as e:
            logger.warning(f"⚠️ Database connection creation failed: {e}")
            logger.info("💡 Database operations will be unavailable until connection is established")
            self._connection = None
        except Exception as e:
            logger.warning(f"⚠️ Unexpected error creating connection: {e}")
            logger.info("💡 Database operations will be unavailable until connection is established")
            self._connection = None

    def test_connection(self) -> bool:
        """
        Test the database connection.

        Returns:
            True if connection is successful, False otherwise
        """
        return True

    def close_connection(self):
        """Close all connections."""
        raise NotImplementedError()

    def get_status(self) -> Dict[str, int]:
        """
        Get connection status.

        Returns:
            Dictionary with connection statistics
        """
        raise NotImplementedError()

    @contextmanager
    def get_connection(self):
        """
        Context manager for getting a database connection.

        Yields:
            psycopg2.connection: Database connection

        Example:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM table")
        """
        if not self._connection:
            raise self.ConnectionError("Database connection not initialized")

        connection = None
        try:
            connection = self._connection.getconn()
            yield connection
        except self.ConnectionError as e:
            if connection:
                connection.rollback()
            logger.error(f"❌ Database operation failed: {e}")
            raise
        finally:
            if connection:
                self._connection.putconn(connection)

    # DB OPERATIONS
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
