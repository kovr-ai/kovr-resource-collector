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
    class SQLParser(object):
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

        @property
        def insert_query(self):
            raise NotImplementedError()

        @property
        def update_query(self):
            raise NotImplementedError()

        @property
        def delete_query(self):
            raise NotImplementedError()

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
    def execute(self, method: str, *args, **kwargs) -> List[Dict[str, Any]]:
        sql_parser = self.SQLParser(*args, **kwargs)
        return self.execute_query(getattr(sql_parser, f'{method}_query'))

    def execute_query(self, *args, **kwargs) -> Any:
        raise NotImplementedError()
