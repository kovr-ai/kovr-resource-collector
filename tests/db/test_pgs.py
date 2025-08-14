"""Tests for PostgreSQL Database operations."""
import os
import tempfile
import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List
import psycopg2

# Import the PostgreSQL database class directly
from con_mon_v2.utils.db.pgs import PostgreSQLDatabase, get_db as get_pgs_db


class TestPostgreSQLDatabase:
    """Test suite for PostgreSQL database operations."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        # Reset singleton instance for clean tests
        PostgreSQLDatabase._instance = None
        PostgreSQLDatabase._initialized = False
    
    def teardown_method(self):
        """Clean up after each test."""
        # Reset singleton instance
        PostgreSQLDatabase._instance = None
        PostgreSQLDatabase._initialized = False
    
    @patch('con_mon_v2.utils.db.pgs.settings')
    @patch('psycopg2.pool.SimpleConnectionPool')
    def test_singleton_pattern(self, mock_pool, mock_settings):
        """Test that PostgreSQLDatabase follows singleton pattern."""
        print("\n🧪 Testing PostgreSQL Database Singleton Pattern...")
        
        # Mock settings
        mock_settings.DB_HOST = 'localhost'
        mock_settings.DB_PORT = 5432
        mock_settings.DB_NAME = 'test_db'
        mock_settings.DB_USER = 'test_user'
        mock_settings.DB_PASSWORD = 'test_pass'
        
        # Test 1: Normal singleton behavior
        db1 = PostgreSQLDatabase()
        db2 = PostgreSQLDatabase()
        
        # Update module-level instance to match current singleton for testing
        import con_mon_v2.utils.db.pgs
        con_mon_v2.utils.db.pgs.db = db1
        db3 = get_pgs_db()
        
        # Verify they are all the same instance
        assert db1 is db2, "PostgreSQLDatabase should follow singleton pattern"
        assert db1 is db3, "get_db() should return the same singleton instance"
        assert db2 is db3, "All instances should be identical"
        
        print("✅ Normal singleton pattern test passed")
        
        # Test 2: Manual recreation for testing purposes only
        print("🧪 Testing manual singleton recreation...")
        
        # Store original instance
        original_instance = PostgreSQLDatabase._instance
        
        # Manually reset for testing purposes (both class and module level)
        PostgreSQLDatabase._instance = None
        PostgreSQLDatabase._initialized = False
        
        # Also reset the module-level instance for complete testing
        import con_mon_v2.utils.db.pgs
        original_module_db = con_mon_v2.utils.db.pgs.db
        
        # Create new instances after reset
        db4 = PostgreSQLDatabase()
        db5 = PostgreSQLDatabase()
        
        # Update module-level instance to the new singleton for testing
        con_mon_v2.utils.db.pgs.db = db4
        db6 = get_pgs_db()
        
        # Verify new instances are also singletons
        assert db4 is db5, "PostgreSQLDatabase should maintain singleton pattern after reset"
        assert db4 is db6, "get_db() should return current singleton after reset"
        assert db5 is db6, "All new instances should be identical"
        
        # Verify new instance is different from original (proving reset worked)
        assert db4 is not original_instance, "New instance should be different from original after reset"
        
        # Restore original module-level instance
        con_mon_v2.utils.db.pgs.db = original_module_db
        
        print("✅ Manual singleton recreation test passed")
        print("✅ PostgreSQL singleton pattern test completed successfully")
    
    @patch('con_mon_v2.utils.db.pgs.settings')
    @patch('psycopg2.pool.SimpleConnectionPool')
    def test_initialization_success(self, mock_pool, mock_settings):
        """Test successful database initialization."""
        print("\n🧪 Testing PostgreSQL Database Initialization...")
        
        # Mock settings
        mock_settings.DB_HOST = 'localhost'
        mock_settings.DB_PORT = 5432
        mock_settings.DB_NAME = 'test_db'
        mock_settings.DB_USER = 'test_user'
        mock_settings.DB_PASSWORD = 'test_pass'
        
        # Mock connection pool
        mock_pool_instance = Mock()
        mock_pool.return_value = mock_pool_instance
        
        # Create database instance
        db = PostgreSQLDatabase()
        
        # Verify initialization
        assert db._initialized == True, "Database should be marked as initialized"
        assert db._connection is mock_pool_instance, "Connection pool should be set"
        
        # Verify connection pool was created with correct parameters
        mock_pool.assert_called_once_with(
            minconn=1,
            maxconn=10,
            host='localhost',
            port=5432,
            database='test_db',
            user='test_user',
            password='test_pass'
        )
        
        print("✅ PostgreSQL initialization test passed")
    
    @patch('con_mon_v2.utils.db.pgs.settings')
    @patch('psycopg2.pool.SimpleConnectionPool')
    def test_initialization_failure(self, mock_pool, mock_settings):
        """Test database initialization failure handling."""
        print("\n🧪 Testing PostgreSQL Database Initialization Failure...")
        
        # Mock settings
        mock_settings.DB_HOST = 'localhost'
        mock_settings.DB_PORT = 5432
        mock_settings.DB_NAME = 'test_db'
        mock_settings.DB_USER = 'test_user'
        mock_settings.DB_PASSWORD = 'test_pass'
        
        # Mock connection pool to raise exception
        mock_pool.side_effect = psycopg2.Error("Connection failed")
        
        # Create database instance
        db = PostgreSQLDatabase()
        
        # Verify graceful failure
        assert db._initialized == True, "Database should still be marked as initialized"
        assert db._connection is None, "Connection pool should be None on failure"
        
        print("✅ PostgreSQL initialization failure test passed")
    
    @patch('con_mon_v2.utils.db.pgs.settings')
    @patch('psycopg2.pool.SimpleConnectionPool')
    def test_execute_query_success(self, mock_pool, mock_settings):
        """Test successful query execution returning list of dictionaries."""
        print("\n🧪 Testing PostgreSQL Query Execution...")
        
        # Mock settings
        mock_settings.DB_HOST = 'localhost'
        mock_settings.DB_PORT = 5432
        mock_settings.DB_NAME = 'test_db'
        mock_settings.DB_USER = 'test_user'
        mock_settings.DB_PASSWORD = 'test_pass'
        
        # Mock connection and cursor
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_connection.cursor.return_value.__exit__ = Mock(return_value=None)
        
        # Mock pool
        mock_pool_instance = Mock()
        mock_pool_instance.getconn.return_value = mock_connection
        mock_pool.return_value = mock_pool_instance
        
        # Mock cursor results - test with nested dictionaries
        mock_cursor.description = [('id',), ('name',), ('metadata',), ('created_at',)]
        mock_cursor.fetchall.return_value = [
            (1, 'Test Item 1', '{"key": "value1", "nested": {"field": "data1"}}', '2024-01-01'),
            (2, 'Test Item 2', '{"key": "value2", "nested": {"field": "data2"}}', '2024-01-02')
        ]
        
        # Create database and execute query
        db = PostgreSQLDatabase()
        results = db.execute_query("SELECT * FROM test_table")
        
        # Verify results format - should be list of dictionaries
        assert isinstance(results, list), "Results should be a list"
        assert len(results) == 2, "Should return 2 rows"
        
        # Verify first row structure
        first_row = results[0]
        assert isinstance(first_row, dict), "Each row should be a dictionary"
        assert first_row['id'] == 1, "ID should be correctly mapped"
        assert first_row['name'] == 'Test Item 1', "Name should be correctly mapped"
        assert first_row['metadata'] == '{"key": "value1", "nested": {"field": "data1"}}', "Nested data should be preserved"
        assert first_row['created_at'] == '2024-01-01', "Date should be correctly mapped"
        
        # Verify second row
        second_row = results[1]
        assert second_row['id'] == 2, "Second row ID should be correct"
        assert second_row['name'] == 'Test Item 2', "Second row name should be correct"
        
        # Verify cursor was called correctly
        mock_cursor.execute.assert_called_once_with("SELECT * FROM test_table", None)
        
        print("✅ PostgreSQL query execution test passed")
    
    @patch('con_mon_v2.utils.db.pgs.settings')
    @patch('psycopg2.pool.SimpleConnectionPool')
    def test_execute_query_with_params(self, mock_pool, mock_settings):
        """Test query execution with parameters."""
        print("\n🧪 Testing PostgreSQL Query with Parameters...")
        
        # Setup mocks
        mock_settings.DB_HOST = 'localhost'
        mock_settings.DB_PORT = 5432
        mock_settings.DB_NAME = 'test_db'
        mock_settings.DB_USER = 'test_user'
        mock_settings.DB_PASSWORD = 'test_pass'
        
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_connection.cursor.return_value.__exit__ = Mock(return_value=None)
        
        mock_pool_instance = Mock()
        mock_pool_instance.getconn.return_value = mock_connection
        mock_pool.return_value = mock_pool_instance
        
        # Mock results with complex nested structure
        mock_cursor.description = [('id',), ('config',), ('settings',)]
        mock_cursor.fetchall.return_value = [
            (1, '{"database": {"host": "localhost", "port": 5432}}', '{"features": ["auth", "logging"]}')
        ]
        
        # Execute query with parameters
        db = PostgreSQLDatabase()
        results = db.execute_query("SELECT * FROM config WHERE id = %s", (1,))
        
        # Verify results
        assert len(results) == 1, "Should return 1 row"
        row = results[0]
        assert row['id'] == 1, "ID should match parameter"
        assert '{"database":' in row['config'], "Config should contain nested JSON"
        assert '{"features":' in row['settings'], "Settings should contain nested JSON"
        
        # Verify parameters were passed correctly
        mock_cursor.execute.assert_called_once_with("SELECT * FROM config WHERE id = %s", (1,))
        
        print("✅ PostgreSQL parameterized query test passed")
    
    @patch('con_mon_v2.utils.db.pgs.settings')
    @patch('psycopg2.pool.SimpleConnectionPool')
    def test_execute_insert(self, mock_pool, mock_settings):
        """Test INSERT operation."""
        print("\n🧪 Testing PostgreSQL INSERT Operation...")
        
        # Setup mocks
        mock_settings.DB_HOST = 'localhost'
        mock_settings.DB_PORT = 5432
        mock_settings.DB_NAME = 'test_db'
        mock_settings.DB_USER = 'test_user'
        mock_settings.DB_PASSWORD = 'test_pass'
        
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_connection.cursor.return_value.__exit__ = Mock(return_value=None)
        
        mock_pool_instance = Mock()
        mock_pool_instance.getconn.return_value = mock_connection
        mock_pool.return_value = mock_pool_instance
        
        # Mock INSERT result with returned ID
        mock_cursor.description = [('id',)]
        mock_cursor.fetchone.return_value = (123,)
        
        # Execute INSERT via generic execute_query
        db = PostgreSQLDatabase()
        db._connection = mock_pool_instance
        results = db.execute_query(
            "INSERT INTO items (name, data) VALUES (%s, %s) RETURNING id",
            ('Test Item', '{"nested": {"key": "value"}}')
        )
        result_id = results[0]['id'] if results and 'id' in results[0] else None
        
        # Verify result
        assert result_id == 123, "Should return inserted row ID"
        
        # Verify commit was called
        mock_connection.commit.assert_called_once()
        
        print("✅ PostgreSQL INSERT test passed")
    
    @patch('con_mon_v2.utils.db.pgs.settings')
    @patch('psycopg2.pool.SimpleConnectionPool')
    def test_execute_update(self, mock_pool, mock_settings):
        """Test UPDATE operation."""
        print("\n🧪 Testing PostgreSQL UPDATE Operation...")
        
        # Setup mocks
        mock_settings.DB_HOST = 'localhost'
        mock_settings.DB_PORT = 5432
        mock_settings.DB_NAME = 'test_db'
        mock_settings.DB_USER = 'test_user'
        mock_settings.DB_PASSWORD = 'test_pass'
        
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_connection.cursor.return_value.__exit__ = Mock(return_value=None)
        mock_cursor.rowcount = 2  # 2 rows affected
        
        mock_pool_instance = Mock()
        mock_pool_instance.getconn.return_value = mock_connection
        mock_pool.return_value = mock_pool_instance
        
        # Execute UPDATE
        db = PostgreSQLDatabase()
        db._connection = mock_pool_instance
        mock_cursor.description = [('rowcount',)]
        mock_cursor.fetchall.return_value = [(2,)]
        affected_rows = db.execute_query(
            "UPDATE items SET metadata = %s WHERE category = %s RETURNING 1 as rowcount",
            ('{"updated": true, "timestamp": "2024-01-01"}', 'test')
        )[0]['rowcount']
        
        # Verify result
        assert affected_rows == 2, "Should return number of affected rows"
        
        # Verify commit was called
        mock_connection.commit.assert_called_once()
        
        print("✅ PostgreSQL UPDATE test passed")
    
    @patch('con_mon_v2.utils.db.pgs.settings')
    @patch('psycopg2.pool.SimpleConnectionPool')
    def test_execute_delete(self, mock_pool, mock_settings):
        """Test DELETE operation."""
        print("\n🧪 Testing PostgreSQL DELETE Operation...")
        
        # Setup mocks
        mock_settings.DB_HOST = 'localhost'
        mock_settings.DB_PORT = 5432
        mock_settings.DB_NAME = 'test_db'
        mock_settings.DB_USER = 'test_user'
        mock_settings.DB_PASSWORD = 'test_pass'
        
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_connection.cursor.return_value.__exit__ = Mock(return_value=None)
        mock_cursor.rowcount = 3  # 3 rows deleted
        
        mock_pool_instance = Mock()
        mock_pool_instance.getconn.return_value = mock_connection
        mock_pool.return_value = mock_pool_instance
        
        # Execute DELETE
        db = PostgreSQLDatabase()
        db._connection = mock_pool_instance
        mock_cursor.description = [('deleted',)]
        mock_cursor.fetchall.return_value = [(3,)]
        deleted_rows = db.execute_query(
            "DELETE FROM items WHERE created_at < %s RETURNING 1 as deleted",
            ('2024-01-01',)
        )[0]['deleted']
        
        # Verify result
        assert deleted_rows == 3, "Should return number of deleted rows"
        
        # Verify commit was called
        mock_connection.commit.assert_called_once()
        
        print("✅ PostgreSQL DELETE test passed")
    
    @patch('con_mon_v2.utils.db.pgs.settings')
    @patch('psycopg2.pool.SimpleConnectionPool')
    def test_connection_error_handling(self, mock_pool, mock_settings):
        """Test database connection error handling."""
        print("\n🧪 Testing PostgreSQL Connection Error Handling...")
        
        # Setup mocks
        mock_settings.DB_HOST = 'localhost'
        mock_settings.DB_PORT = 5432
        mock_settings.DB_NAME = 'test_db'
        mock_settings.DB_USER = 'test_user'
        mock_settings.DB_PASSWORD = 'test_pass'
        
        mock_pool_instance = Mock()
        mock_pool_instance.getconn.side_effect = psycopg2.Error("Connection failed")
        mock_pool.return_value = mock_pool_instance
        
        # Test query execution with connection error
        db = PostgreSQLDatabase()
        
        with pytest.raises(psycopg2.Error):
            db.execute_query("SELECT * FROM test_table")
        
        print("✅ PostgreSQL connection error handling test passed")
    
    @patch('con_mon_v2.utils.db.pgs.settings')
    @patch('psycopg2.pool.SimpleConnectionPool')
    def test_test_connection(self, mock_pool, mock_settings):
        """Test connection testing functionality."""
        print("\n🧪 Testing PostgreSQL Connection Test...")
        
        # Setup mocks
        mock_settings.DB_HOST = 'localhost'
        mock_settings.DB_PORT = 5432
        mock_settings.DB_NAME = 'test_db'
        mock_settings.DB_USER = 'test_user'
        mock_settings.DB_PASSWORD = 'test_pass'
        
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_connection.cursor.return_value.__exit__ = Mock(return_value=None)
        mock_cursor.fetchone.return_value = (1,)
        
        mock_pool_instance = Mock()
        mock_pool_instance.getconn.return_value = mock_connection
        mock_pool.return_value = mock_pool_instance
        
        # Test connection
        db = PostgreSQLDatabase()
        result = db.test_connection()
        
        # Verify result
        assert result == True, "Connection test should succeed"
        mock_cursor.execute.assert_called_once_with("SELECT 1")
        
        print("✅ PostgreSQL connection test passed")
    
    @patch('con_mon_v2.utils.db.pgs.settings')
    @patch('psycopg2.pool.SimpleConnectionPool')
    def test_complex_nested_data_handling(self, mock_pool, mock_settings):
        """Test handling of complex nested data structures."""
        print("\n🧪 Testing PostgreSQL Complex Nested Data Handling...")
        
        # Setup mocks
        mock_settings.DB_HOST = 'localhost'
        mock_settings.DB_PORT = 5432
        mock_settings.DB_NAME = 'test_db'
        mock_settings.DB_USER = 'test_user'
        mock_settings.DB_PASSWORD = 'test_pass'
        
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_connection.cursor.return_value.__exit__ = Mock(return_value=None)
        
        mock_pool_instance = Mock()
        mock_pool_instance.getconn.return_value = mock_connection
        mock_pool.return_value = mock_pool_instance
        
        # Complex nested data structure
        complex_metadata = {
            "user": {
                "profile": {
                    "name": "John Doe",
                    "settings": {
                        "theme": "dark",
                        "notifications": ["email", "push"]
                    }
                },
                "permissions": ["read", "write", "admin"]
            },
            "audit": {
                "created_by": "system",
                "modified_by": "admin",
                "timestamps": {
                    "created": "2024-01-01T00:00:00Z",
                    "modified": "2024-01-02T12:30:00Z"
                }
            }
        }
        
        # Mock complex query results
        mock_cursor.description = [('id',), ('metadata',), ('config',)]
        mock_cursor.fetchall.return_value = [
            (1, str(complex_metadata), '{"database": {"pool_size": 10}}')
        ]
        
        # Execute query
        db = PostgreSQLDatabase()
        results = db.execute_query("SELECT id, metadata, config FROM complex_table")
        
        # Verify complex data is preserved as strings (as returned by PostgreSQL)
        assert len(results) == 1, "Should return 1 row"
        row = results[0]
        assert isinstance(row, dict), "Row should be a dictionary"
        assert row['id'] == 1, "ID should be correct"
        assert 'user' in row['metadata'], "Complex metadata should be preserved"
        assert 'profile' in row['metadata'], "Nested structure should be preserved"
        assert 'database' in row['config'], "Config structure should be preserved"
        
        print("✅ PostgreSQL complex nested data handling test passed")


def run_all_tests():
    """Run all PostgreSQL database tests."""
    print("🚀 Starting PostgreSQL Database Tests...")
    
    test_instance = TestPostgreSQLDatabase()
    
    try:
        test_instance.test_singleton_pattern()
        test_instance.test_initialization_success()
        test_instance.test_initialization_failure()
        test_instance.test_execute_query_success()
        test_instance.test_execute_query_with_params()
        test_instance.test_execute_insert()
        test_instance.test_execute_update()
        test_instance.test_execute_delete()
        test_instance.test_connection_error_handling()
        test_instance.test_test_connection()
        test_instance.test_complex_nested_data_handling()
        
        print("\n🎉 All PostgreSQL Database tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    if not success:
        exit(1)
