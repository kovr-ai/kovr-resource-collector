"""
Database singleton for PostgreSQL operations in con_mon.

Provides a singleton pattern for database connections with connection pooling
and methods for executing SQL queries.
"""
import os
import psycopg2
import psycopg2.pool
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
import logging
from con_mon.utils.config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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


# Create singleton instance
db = PostgreSQLDatabase()


def get_db() -> PostgreSQLDatabase:
    """
    Get the database singleton instance.
    
    Returns:
        PostgreSQLDatabase singleton instance
    """
    return db 