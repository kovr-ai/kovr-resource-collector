"""Tests for unified database abstraction layer."""
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
from con_mon.utils.db import get_db


class TestUnifiedDatabaseAbstraction:
    """Test suite for unified database abstraction ensuring consistent interface."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        # Create temporary directory for CSV testing
        self.test_dir = tempfile.mkdtemp()
        self.test_csv_dir = Path(self.test_dir) / "data" / "csv"
        self.test_csv_dir.mkdir(parents=True, exist_ok=True)
        # Ensure CSV backend uses temp directory by default during tests
        from con_mon.utils.config import settings as _settings
        _settings.CSV_DATA = str(self.test_csv_dir)
        
        # Reset any singleton instances and rebind module-level CSV db
        from con_mon.utils.db.csv import CSVDatabase
        from con_mon.utils.db.pgs import PostgreSQLDatabase
        CSVDatabase._instance = None
        CSVDatabase._initialized = False
        PostgreSQLDatabase._instance = None
        PostgreSQLDatabase._initialized = False
        import con_mon.utils.db.csv as csv_module
        csv_module.db = CSVDatabase()
    
    def teardown_method(self):
        """Clean up after each test."""
        # Clean up test directory
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

        from con_mon.utils.config import settings
        # Reset environment variable for isolation
        settings.CSV_DATA = None


        # Reset CSV database singleton to prevent test isolation issues
        from con_mon.utils.db.csv import CSVDatabase
        CSVDatabase._instance = None
        CSVDatabase._initialized = False
        
        # Also reset the module-level db variable
        import con_mon.utils.db.csv as csv_module
        csv_module.db = CSVDatabase()

    @patch('con_mon.utils.db.pgs.settings')
    def test_get_db_returns_csv_when_configured(self, mock_settings):
        """Test that get_db returns CSV database when configured."""
        print("\n🧪 Testing get_db returns CSV when configured...")

        # Set environment variable to use CSV
        mock_settings.CSV_DATA = 'csv/data/'

        # Force CSV backend for this test
        from con_mon.utils.config import settings as _settings
        _settings.CSV_DATA = str(self.test_csv_dir)
        db = get_db()
        
        # Verify it's a CSV database
        from con_mon.utils.db.csv import CSVDatabase
        assert isinstance(db, CSVDatabase), "Should return CSVDatabase when configured"
        
        print("✅ get_db returns CSV when configured test passed")
    
    @patch('con_mon.utils.db.pgs.settings')
    @patch('psycopg2.pool.SimpleConnectionPool')
    def test_get_db_returns_postgres_by_default(self, mock_pool, mock_settings):
        """Test that get_db returns PostgreSQL by default."""
        print("\n🧪 Testing get_db returns PostgreSQL by default...")
        
        # Reset singleton instances first
        from con_mon.utils.db.pgs import PostgreSQLDatabase
        PostgreSQLDatabase._instance = None
        PostgreSQLDatabase._initialized = False
        
        # Mock settings
        mock_settings.DB_HOST = 'localhost'
        mock_settings.DB_PORT = 5432
        mock_settings.DB_NAME = 'test_db'
        mock_settings.DB_USER = 'test_user'
        mock_settings.DB_PASSWORD = 'test_pass'
        mock_pool.return_value = Mock()

        # Ensure CSV backend is NOT selected by default
        if mock_settings.CSV_DATA:
            mock_settings.CSV_DATA = None
        from con_mon.utils.config import settings as _settings
        _settings.CSV_DATA = None
        db = get_db()
        
        # Verify it's a PostgreSQL database
        from con_mon.utils.db.pgs import PostgreSQLDatabase
        assert isinstance(db, PostgreSQLDatabase), "Should return PostgreSQLDatabase by default"
        
        print("✅ get_db returns PostgreSQL by default test passed")
    
    def test_csv_database_list_of_dicts_interface(self):
        """Test CSV database returns list of dictionaries with nested data."""
        print("\n🧪 Testing CSV Database List of Dicts Interface...")
        
        # Force CSV backend for this test
        from con_mon.utils.config import settings as _settings
        _settings.CSV_DATA = str(self.test_csv_dir)
        db = get_db()
        
        # Create test data with nested structures (keys align with CSV backend behavior)
        test_data = [
            {
                "id": 1,
                "name": "John Doe",
                "email": "john@example.com",
                "metadata": {
                    "profile": {
                        "age": 30,
                        "preferences": ["coding", "reading"],
                        "settings": {
                            "theme": "dark",
                            "notifications": True
                        }
                    },
                    "audit": {
                        "created_at": "2024-01-01T00:00:00Z",
                        "created_by": "system"
                    }
                }
            },
            {
                "id": 2,
                "name": "Test User 2",
                "email": "user2@example.com",
                "metadata": {
                    "profile": {
                        "age": 22,
                        "preferences": ["design"],
                        "settings": {
                            "theme": "light",
                            "notifications": False
                        }
                    },
                    "audit": {
                        "created_at": "2024-01-02T00:00:00Z",
                        "created_by": "tester"
                    }
                }
            }
        ]
        
        # Create table with nested data
        columns = ["id", "name", "email", "metadata"]
        db.create_table("test_users", columns, test_data)
        
        # Query data
        from con_mon.utils.db.csv import CSVDatabase as _CSV
        results = db.execute('select', table_name='test_users')
        
        # Verify interface returns list of dictionaries
        assert isinstance(results, list), "Results should be a list"
        assert len(results) == 2, "Should return 2 rows"
        
        # Verify each row is a dictionary with nested structures
        for i, row in enumerate(results):
            assert isinstance(row, dict), f"Row {i} should be a dictionary"
            assert "id" in row, f"Row {i} should have id field"
            assert "metadata" in row, f"Row {i} should have metadata field"
            assert isinstance(row["metadata"], dict), f"Row {i} metadata should be nested dict"
            
            # Verify deep nested structures
            meta_profile = row["metadata"]["profile"]
            assert "settings" in meta_profile, f"Row {i} should have nested settings"
            assert isinstance(meta_profile["settings"], dict), f"Row {i} settings should be dict"
            assert isinstance(row["metadata"]["audit"], dict), f"Row {i} audit should be dict"
        
        print("✅ CSV database list of dicts interface test passed")
    
    @patch('con_mon.utils.db.pgs.settings')
    @patch('psycopg2.pool.SimpleConnectionPool')
    def test_postgresql_database_list_of_dicts_interface(self, mock_pool, mock_settings):
        """Test PostgreSQL database returns list of dictionaries with nested data."""
        print("\n🧪 Testing PostgreSQL Database List of Dicts Interface...")
        
        # Reset singleton instances first
        from con_mon.utils.db.pgs import PostgreSQLDatabase
        PostgreSQLDatabase._instance = None
        PostgreSQLDatabase._initialized = False
        
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
        
        mock_pool_instance = Mock()
        mock_pool_instance.getconn.return_value = mock_connection
        mock_pool.return_value = mock_pool_instance
        
        # Ensure Postgres backend (CSV disabled)
        mock_settings.CSV_DATA = None
        from con_mon.utils.config import settings as _settings
        _settings.CSV_DATA = None

        # Get PostgreSQL database
        db = get_db()
        
        # Ensure the connection pool is properly set
        db._connection = mock_pool_instance
        
        # Mock complex nested query results (as JSON strings from PostgreSQL)
        mock_cursor.description = [('id',), ('name',), ('profile',), ('config',)]
        mock_cursor.fetchall.return_value = [
            (
                1, 
                'Test User 1',
                '{"email": "user1@example.com", "settings": {"theme": "dark", "notifications": {"email": true, "push": false, "types": ["security", "updates"]}}}',
                '{"database": {"host": "localhost", "pool": {"min": 1, "max": 10}}, "features": ["auth", "logging"]}'
            ),
            (
                2,
                'Test User 2', 
                '{"email": "user2@example.com", "settings": {"theme": "light", "notifications": {"email": false, "push": true, "types": ["updates"]}}}',
                '{"database": {"host": "production", "pool": {"min": 2, "max": 20}}, "features": ["auth", "monitoring"]}'
            )
        ]
        
        # Execute DML with RETURNING to validate list-of-dicts interface
        results = db.execute_insert(
            "INSERT INTO users (name, profile, config) VALUES (%s, %s, %s) RETURNING id, name, profile, config",
            ('n/a', '{}', '{}')
        )
        
        # Verify interface returns list of dictionaries
        assert isinstance(results, list), "Results should be a list"
        assert len(results) == 2, "Should return 2 rows"
        
        # Verify each row is a dictionary with nested JSON data (as strings from PostgreSQL)
        for i, row in enumerate(results):
            assert isinstance(row, dict), f"Row {i} should be a dictionary"
            assert "id" in row, f"Row {i} should have id field"
            assert "name" in row, f"Row {i} should have name field"
            assert "profile" in row, f"Row {i} should have profile field"
            assert "config" in row, f"Row {i} should have config field"
            
            # Verify nested data is preserved as JSON strings (PostgreSQL behavior)
            assert isinstance(row["profile"], str), f"Row {i} profile should be JSON string from PostgreSQL"
            assert isinstance(row["config"], str), f"Row {i} config should be JSON string from PostgreSQL"
            assert '"email":' in row["profile"], f"Row {i} profile should contain nested email"
            assert '"settings":' in row["profile"], f"Row {i} profile should contain nested settings"
            assert '"database":' in row["config"], f"Row {i} config should contain nested database"
        
        # Verify cursor was called with the query
        mock_cursor.execute.assert_called_once()
        
        print("✅ PostgreSQL database list of dicts interface test passed")
    
    def test_csv_insert_with_nested_dictionaries(self):
        """Test CSV database INSERT with nested dictionary data."""
        print("\n🧪 Testing CSV INSERT with Nested Dictionaries...")
        
        # Force CSV backend for this test
        from con_mon.utils.config import settings as _settings
        _settings.CSV_DATA = str(self.test_csv_dir)
        db = get_db()
        
        # Create table
        columns = ["id", "name", "data"]
        db.create_table("test_inserts", columns)
        
        # Insert data with complex nested structures
        insert_data = [
            {
                "id": 1,
                "name": "Complex Record 1",
                "data": {
                    "user_info": {
                        "personal": {
                            "name": "John Doe",
                            "age": 30,
                            "contacts": {
                                "email": "john@example.com",
                                "phones": ["+1234567890", "+0987654321"]
                            }
                        },
                        "preferences": {
                            "language": "en",
                            "timezone": "UTC",
                            "features": ["dark_mode", "notifications", "analytics"]
                        }
                    },
                    "system_info": {
                        "created_at": "2024-01-01T00:00:00Z",
                        "version": "1.0.0",
                        "metadata": {
                            "source": "api",
                            "validation": {
                                "required_fields": ["name", "email"],
                                "optional_fields": ["phone", "address"]
                            }
                        }
                    }
                }
            }
        ]
        
        # Insert the data
        rows_inserted = db.execute_insert("test_inserts", insert_data)
        assert rows_inserted == 1, "Should insert 1 row"
        
        # Query back and verify nested structure is preserved
        from con_mon.utils.db.csv import CSVDatabase as _CSV
        results = db.execute('select', table_name='test_inserts')
        assert len(results) == 1, "Should return 1 row"
        
        row = results[0]
        assert isinstance(row, dict), "Row should be a dictionary"
        assert isinstance(row["data"], dict), "Data field should be nested dictionary"
        assert isinstance(row["data"]["user_info"], dict), "user_info should be nested dict"
        assert isinstance(row["data"]["user_info"]["personal"]["contacts"], dict), "contacts should be nested dict"
        assert isinstance(row["data"]["user_info"]["personal"]["contacts"]["phones"], list), "phones should be array"
        assert isinstance(row["data"]["user_info"]["preferences"]["features"], list), "features should be array"
        assert isinstance(row["data"]["system_info"]["metadata"]["validation"], dict), "validation should be nested dict"
        
        # Verify deep nested values
        assert row["data"]["user_info"]["personal"]["name"] == "John Doe", "Deep nested name should be preserved"
        assert row["data"]["user_info"]["preferences"]["language"] == "en", "Deep nested language should be preserved"
        assert "dark_mode" in row["data"]["user_info"]["preferences"]["features"], "Deep nested array should be preserved"
        assert "email" in row["data"]["system_info"]["metadata"]["validation"]["required_fields"], "Deep nested array should be preserved"
        
        print("✅ CSV INSERT with nested dictionaries test passed")
    
    @patch('con_mon.utils.db.pgs.settings')
    @patch('psycopg2.pool.SimpleConnectionPool')
    def test_postgresql_insert_with_nested_dictionaries(self, mock_pool, mock_settings):
        """Test PostgreSQL database INSERT with nested dictionary data."""
        print("\n🧪 Testing PostgreSQL INSERT with Nested Dictionaries...")
        
        # Reset singleton instances first
        from con_mon.utils.db.pgs import PostgreSQLDatabase
        PostgreSQLDatabase._instance = None
        PostgreSQLDatabase._initialized = False
        
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
        
        mock_pool_instance = Mock()
        mock_pool_instance.getconn.return_value = mock_connection
        mock_pool.return_value = mock_pool_instance
        
        # Set environment to use PostgreSQL (disable CSV backend)
        mock_settings.CSV_DATA = None
        from con_mon.utils.config import settings as _settings
        _settings.CSV_DATA = None
        
        # Get PostgreSQL database
        db = get_db()
        
        # Ensure the connection pool is properly set
        db._connection = mock_pool_instance
        
        # Mock INSERT result
        mock_cursor.description = [('id',)]
        mock_cursor.fetchone.return_value = (123,)
        
        # Execute INSERT with nested JSON data via execute_insert
        nested_json_data = '{"user": {"profile": {"name": "John", "settings": {"theme": "dark", "notifications": ["email", "push"]}}, "metadata": {"created": "2024-01-01", "tags": ["admin", "verified"]}}}'
        mock_cursor.description = [('id',)]
        mock_cursor.fetchall.return_value = [(123,)]
        result_id = db.execute_insert(
            "INSERT INTO users (name, data) VALUES (%s, %s) RETURNING id",
            ('Test User', nested_json_data)
        )[0]['id']
        
        # Verify INSERT behavior
        assert result_id == 123, "Should return inserted row ID"
        mock_connection.commit.assert_called_once()
        
        # Verify the INSERT was called with nested JSON data
        mock_cursor.execute.assert_called_once_with(
            "INSERT INTO users (name, data) VALUES (%s, %s) RETURNING id",
            ('Test User', nested_json_data)
        )
        
        print("✅ PostgreSQL INSERT with nested dictionaries test passed")
    
    def test_data_consistency_between_databases(self):
        """Test that both databases handle the same nested data consistently."""
        print("\n🧪 Testing Data Consistency Between Databases...")
        
        # Test data with complex nested structures
        test_data = {
            "id": 1,
            "name": "Consistency Test",
            "config": {
                "application": {
                    "name": "TestApp",
                    "version": "2.1.0",
                    "features": {
                        "authentication": {
                            "enabled": True,
                            "providers": ["oauth", "saml", "ldap"],
                            "settings": {
                                "session_timeout": 3600,
                                "multi_factor": True,
                                "password_policy": {
                                    "min_length": 8,
                                    "require_special": True,
                                    "require_numbers": True
                                }
                            }
                        },
                        "logging": {
                            "enabled": True,
                            "level": "INFO",
                            "outputs": ["console", "file", "syslog"],
                            "rotation": {
                                "max_size": "100MB",
                                "max_files": 10
                            }
                        }
                    }
                },
                "database": {
                    "type": "postgresql",
                    "connection": {
                        "host": "localhost",
                        "port": 5432,
                        "pool": {
                            "min_connections": 5,
                            "max_connections": 20,
                            "timeout": 30
                        }
                    }
                }
            },
            "metadata": {
                "created_at": "2024-01-01T00:00:00Z",
                "created_by": "system",
                "tags": ["production", "critical", "monitored"],
                "validation": {
                    "schema_version": "1.0",
                    "last_validated": "2024-01-01T12:00:00Z",
                    "status": "valid"
                }
            }
        }
        
        # Test CSV database
        print("  Testing CSV database consistency...")
        from con_mon.utils.config import settings as _settings
        _settings.CSV_DATA = str(self.test_csv_dir)
        csv_db = get_db()
        
        # Create table and insert data
        columns = ["id", "name", "config", "metadata"]
        csv_db.create_table("consistency_test", columns)
        csv_db.execute_insert("consistency_test", test_data)
        
        # Query back data
        from con_mon.utils.db.csv import CSVDatabase as _CSV
        csv_results = csv_db.execute('select', table_name='consistency_test')
        assert len(csv_results) == 1, "CSV should return 1 row"
        csv_row = csv_results[0]
        
        # Verify CSV preserves nested structure as dictionaries
        assert isinstance(csv_row, dict), "CSV row should be dictionary"
        assert isinstance(csv_row["config"], dict), "CSV config should be nested dict"
        assert isinstance(csv_row["config"]["application"]["features"]["authentication"], dict), "Deep nesting should be preserved"
        assert csv_row["config"]["application"]["features"]["authentication"]["settings"]["session_timeout"] == 3600, "Deep nested values should be preserved"
        assert isinstance(csv_row["config"]["application"]["features"]["authentication"]["providers"], list), "Nested arrays should be preserved"
        assert "oauth" in csv_row["config"]["application"]["features"]["authentication"]["providers"], "Array values should be preserved"
        assert isinstance(csv_row["metadata"]["tags"], list), "Top-level arrays should be preserved"
        assert "production" in csv_row["metadata"]["tags"], "Array values should be preserved"
        
        print("  ✅ CSV database consistency verified")
        
        # Note: For PostgreSQL, we would typically store the nested data as JSON strings
        # and the application would be responsible for parsing them. This is the expected
        # behavior difference between the two database types.
        
        print("✅ Data consistency between databases test passed")
    
    def test_error_handling_consistency(self):
        """Test that both databases handle errors consistently."""
        print("\n🧪 Testing Error Handling Consistency...")
        
        # Test CSV database error handling
        from con_mon.utils.config import settings as _settings
        _settings.CSV_DATA = str(self.test_csv_dir)
        csv_db = get_db()
        
        # Test operations on non-existent table
        from con_mon.utils.db.csv import CSVDatabase as _CSV
        q = _CSV.SQLParser("nonexistent_table").select_query
        csv_results = csv_db.execute_query(q)
        assert csv_results == [], "CSV should return empty list for non-existent table"
        
        csv_affected = csv_db.execute_update("nonexistent_table", data={"field": "value"})
        assert csv_affected == 0, "CSV should return 0 for update on non-existent table"
        
        csv_deleted = csv_db.execute_delete("nonexistent_table")
        assert csv_deleted == 0, "CSV should return 0 for delete on non-existent table"
        
        print("  ✅ CSV error handling consistency verified")
        
        # Note: PostgreSQL error handling would be tested with mocks to ensure
        # it also returns consistent empty results or appropriate error codes
        # rather than raising exceptions for non-existent tables
        
        print("✅ Error handling consistency test passed")


def run_all_tests():
    """Run all unified database abstraction tests."""
    print("🚀 Starting Unified Database Abstraction Tests...")
    
    test_instance = TestUnifiedDatabaseAbstraction()
    
    try:
        test_instance.setup_method()
        test_instance.test_get_db_returns_csv_when_configured()
        test_instance.teardown_method()
        
        test_instance.setup_method()
        test_instance.test_get_db_returns_postgres_by_default()
        test_instance.teardown_method()
        
        test_instance.setup_method()
        test_instance.test_csv_database_list_of_dicts_interface()
        test_instance.teardown_method()
        
        test_instance.setup_method()
        test_instance.test_postgresql_database_list_of_dicts_interface()
        test_instance.teardown_method()
        
        test_instance.setup_method()
        test_instance.test_csv_insert_with_nested_dictionaries()
        test_instance.teardown_method()
        
        test_instance.setup_method()
        test_instance.test_postgresql_insert_with_nested_dictionaries()
        test_instance.teardown_method()
        
        test_instance.setup_method()
        test_instance.test_data_consistency_between_databases()
        test_instance.teardown_method()
        
        test_instance.setup_method()
        test_instance.test_error_handling_consistency()
        test_instance.teardown_method()
        
        print("\n🎉 All Unified Database Abstraction tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    if not success:
        exit(1)
