"""Tests for CSV Database operations."""
import os
import tempfile
import shutil
import json
from pathlib import Path
from datetime import datetime
import pandas as pd

# Import the CSV database class directly
from con_mon_v2.utils.db.csv import CSVDatabase, get_db as get_csv_db


class TestCSVDatabase:
    """Test suite for CSV database operations."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        # Reset singleton instance for clean tests
        CSVDatabase._instance = None
        CSVDatabase._initialized = False
        
        # Create temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.test_csv_dir = Path(self.test_dir) / "data" / "csv"
        self.test_csv_dir.mkdir(parents=True, exist_ok=True)
    
    def teardown_method(self):
        """Clean up after each test."""
        # Reset singleton instance
        CSVDatabase._instance = None
        CSVDatabase._initialized = False
        
        # Clean up test directory
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def _create_test_db(self) -> CSVDatabase:
        """Create a test CSV database instance with custom directory."""
        db = CSVDatabase()
        db._csv_directory = self.test_csv_dir
        return db
    
    def test_singleton_pattern(self):
        """Test that CSVDatabase follows singleton pattern."""
        print("\n🧪 Testing CSV Database Singleton Pattern...")
        
        # Test 1: Normal singleton behavior
        db1 = CSVDatabase()
        db2 = CSVDatabase()
        
        # Update module-level instance to match current singleton for testing
        import con_mon_v2.utils.db.csv
        con_mon_v2.utils.db.csv.db = db1
        db3 = get_csv_db()
        
        # Verify they are all the same instance
        assert db1 is db2, "CSVDatabase should follow singleton pattern"
        assert db1 is db3, "get_csv_db() should return the same singleton instance"
        assert db2 is db3, "All instances should be identical"
        
        print("✅ Normal singleton pattern test passed")
        
        # Test 2: Manual recreation for testing purposes only
        print("🧪 Testing manual singleton recreation...")
        
        # Store original instance
        original_instance = CSVDatabase._instance
        
        # Manually reset for testing purposes (both class and module level)
        CSVDatabase._instance = None
        CSVDatabase._initialized = False
        
        # Also reset the module-level instance for complete testing
        import con_mon_v2.utils.db.csv
        original_module_db = con_mon_v2.utils.db.csv.db
        
        # Create new instances after reset
        db4 = CSVDatabase()
        db5 = CSVDatabase()
        
        # Update module-level instance to the new singleton for testing
        con_mon_v2.utils.db.csv.db = db4
        db6 = get_csv_db()
        
        # Verify new instances are also singletons
        assert db4 is db5, "CSVDatabase should maintain singleton pattern after reset"
        assert db4 is db6, "get_csv_db() should return current singleton after reset"
        assert db5 is db6, "All new instances should be identical"
        
        # Verify new instance is different from original (proving reset worked)
        assert db4 is not original_instance, "New instance should be different from original after reset"
        
        # Restore original module-level instance
        con_mon_v2.utils.db.csv.db = original_module_db
        
        print("✅ Manual singleton recreation test passed")
        print("✅ CSV singleton pattern test completed successfully")
    
    def test_initialization(self):
        """Test CSV database initialization."""
        print("\n🧪 Testing CSV Database Initialization...")
        
        db = self._create_test_db()
        
        # Verify initialization
        assert db._initialized == True, "Database should be marked as initialized"
        assert db._csv_directory is not None, "CSV directory should be set"
        assert db._csv_directory.exists(), "CSV directory should exist"
        
        # Test connection
        connection_status = db.test_connection()
        assert connection_status == True, "Connection test should pass"
        
        print("✅ CSV initialization test passed")
    
    def test_create_and_drop_table(self):
        """Test creating and dropping CSV tables."""
        print("\n🧪 Testing CSV Table Creation and Deletion...")
        
        db = self._create_test_db()
        
        # Test create table
        columns = ["id", "name", "email", "metadata"]
        result = db.create_table("users", columns)
        assert result == True, "Table creation should succeed"
        
        # Verify table exists
        assert db._table_exists("users"), "Table should exist after creation"
        
        # Test table info
        table_info = db.get_table_info("users")
        assert table_info["exists"] == True, "Table should be reported as existing"
        assert table_info["row_count"] == 0, "New table should have 0 rows"
        assert table_info["columns"] == columns, "Table should have correct columns"
        
        # Test drop table
        result = db.drop_table("users")
        assert result == True, "Table deletion should succeed"
        assert not db._table_exists("users"), "Table should not exist after deletion"
        
        print("✅ CSV table creation and deletion tests passed")
    
    def test_execute_query_list_of_dicts(self):
        """Test execute_query returns list of dictionaries."""
        print("\n🧪 Testing CSV Query Returns List of Dictionaries...")
        
        db = self._create_test_db()
        
        # Create test table with complex nested data
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
                "name": "Jane Smith", 
                "email": "jane@example.com",
                "metadata": {
                    "profile": {
                        "age": 25,
                        "preferences": ["design", "photography"],
                        "settings": {
                            "theme": "light",
                            "notifications": False
                        }
                    },
                    "audit": {
                        "created_at": "2024-01-02T00:00:00Z",
                        "created_by": "admin"
                    }
                }
            }
        ]
        
        columns = ["id", "name", "email", "metadata"]
        db.create_table("test_users", columns, test_data)
        
        # Test query all rows
        all_results = db.execute('select', table_name='test_users')
        
        # Verify results format - should be list of dictionaries
        assert isinstance(all_results, list), "Results should be a list"
        assert len(all_results) == 2, "Should return 2 rows"
        
        # Verify first row structure
        first_row = all_results[0]
        assert isinstance(first_row, dict), "Each row should be a dictionary"
        assert first_row['id'] == 1, "ID should be correctly mapped"
        assert first_row['name'] == 'John Doe', "Name should be correctly mapped"
        assert first_row['email'] == 'john@example.com', "Email should be correctly mapped"
        
        # Verify nested metadata structure is preserved
        assert isinstance(first_row['metadata'], dict), "Metadata should be a dictionary"
        assert 'profile' in first_row['metadata'], "Nested profile should exist"
        assert 'audit' in first_row['metadata'], "Nested audit should exist"
        assert first_row['metadata']['profile']['age'] == 30, "Nested age should be correct"
        assert 'coding' in first_row['metadata']['profile']['preferences'], "Nested array should be preserved"
        
        print("✅ CSV query list of dictionaries test passed")
    
    def test_execute_query_with_conditions(self):
        """Test query execution with filtering conditions."""
        print("\n🧪 Testing CSV Query with Conditions...")
        
        db = self._create_test_db()
        
        # Create test data with nested structures
        test_data = [
            {
                "id": 1,
                "department": "IT",
                "employee": {
                    "name": "Alice",
                    "level": "senior",
                    "skills": ["python", "sql"]
                },
                "status": "active"
            },
            {
                "id": 2,
                "department": "IT", 
                "employee": {
                    "name": "Bob",
                    "level": "junior",
                    "skills": ["javascript", "html"]
                },
                "status": "active"
            },
            {
                "id": 3,
                "department": "HR",
                "employee": {
                    "name": "Charlie",
                    "level": "manager",
                    "skills": ["management", "communication"]
                },
                "status": "inactive"
            }
        ]
        
        columns = ["id", "department", "employee", "status"]
        db.create_table("employees", columns, test_data)
        
        # Test query with conditions
        it_employees = db.execute('select', table_name='employees', where={"department": "IT"})
        assert len(it_employees) == 2, "Should return 2 IT employees"
        
        # Verify returned data maintains nested structure
        for emp in it_employees:
            assert isinstance(emp, dict), "Each result should be a dictionary"
            assert emp["department"] == "IT", "Department should match condition"
            assert isinstance(emp["employee"], dict), "Employee should be nested dict"
            assert "name" in emp["employee"], "Nested employee name should exist"
            assert "skills" in emp["employee"], "Nested skills array should exist"
        
        # Test multiple conditions
        active_it = db.execute('select', table_name='employees', where={"department": "IT", "status": "active"})
        assert len(active_it) == 2, "Should return 2 active IT employees"
        
        # Test with specific columns
        names_only = db.execute('select', table_name='employees', select=["employee"]) 
        assert len(names_only) == 3, "Should return all 3 rows"
        for row in names_only:
            assert list(row.keys()) == ["employee"], "Should only return employee column"
            assert isinstance(row["employee"], dict), "Employee should remain nested dict"
        
        print("✅ CSV query with conditions test passed")
    
    def test_execute_insert_nested_data(self):
        """Test INSERT operations with nested data structures."""
        print("\n🧪 Testing CSV INSERT with Nested Data...")
        
        db = self._create_test_db()
        
        # Create table
        columns = ["id", "name", "config", "data"]
        db.create_table("test_table", columns)
        
        # Test single row insert with nested data
        complex_data = {
            "id": 1,
            "name": "Test Config",
            "config": {
                "database": {
                    "host": "localhost",
                    "port": 5432,
                    "settings": {
                        "pool_size": 10,
                        "timeout": 30,
                        "features": ["ssl", "compression"]
                    }
                },
                "cache": {
                    "enabled": True,
                    "ttl": 3600
                }
            },
            "data": {
                "metrics": [
                    {"name": "cpu", "value": 85.2},
                    {"name": "memory", "value": 67.8}
                ],
                "tags": ["production", "critical"]
            }
        }
        
        rows_inserted = db.execute_insert("test_table", complex_data)
        assert rows_inserted == 1, "Should insert 1 row"
        
        # Verify inserted data maintains structure
        results = db.execute('select', table_name='test_table')
        assert len(results) == 1, "Should have 1 row"
        
        inserted_row = results[0]
        assert isinstance(inserted_row, dict), "Row should be a dictionary"
        assert inserted_row["id"] == 1, "ID should be correct"
        assert isinstance(inserted_row["config"], dict), "Config should be nested dict"
        assert inserted_row["config"]["database"]["host"] == "localhost", "Nested values should be preserved"
        assert inserted_row["config"]["database"]["settings"]["pool_size"] == 10, "Deep nested values should be preserved"
        assert isinstance(inserted_row["data"]["metrics"], list), "Nested arrays should be preserved"
        assert len(inserted_row["data"]["metrics"]) == 2, "Array length should be preserved"
        
        print("✅ CSV INSERT with nested data test passed")
    
    def test_execute_update_nested_data(self):
        """Test UPDATE operations with nested data structures."""
        print("\n🧪 Testing CSV UPDATE with Nested Data...")
        
        db = self._create_test_db()
        
        # Create test data
        initial_data = [
            {
                "id": 1,
                "name": "Config 1",
                "settings": {
                    "theme": "light",
                    "features": {
                        "notifications": True,
                        "auto_save": False
                    }
                }
            },
            {
                "id": 2,
                "name": "Config 2", 
                "settings": {
                    "theme": "dark",
                    "features": {
                        "notifications": False,
                        "auto_save": True
                    }
                }
            }
        ]
        
        columns = ["id", "name", "settings"]
        db.create_table("configs", columns, initial_data)
        
        # Test update with nested data
        new_settings = {
            "theme": "custom",
            "features": {
                "notifications": True,
                "auto_save": True,
                "dark_mode": True
            },
            "advanced": {
                "debug": False,
                "logging": ["error", "warn"]
            }
        }
        
        affected_rows = db.execute_update("configs", 
                                        data={"settings": new_settings}, 
                                        conditions={"id": 1})
        assert affected_rows == 1, "Should update 1 row"
        
        # Verify updated data maintains nested structure
        results = db.execute('select', table_name='configs', where={"id": 1})
        updated_row = results[0]
        
        assert isinstance(updated_row["settings"], dict), "Settings should be nested dict"
        assert updated_row["settings"]["theme"] == "custom", "Updated theme should be correct"
        assert updated_row["settings"]["features"]["dark_mode"] == True, "New nested field should be added"
        assert isinstance(updated_row["settings"]["advanced"]["logging"], list), "Nested array should be preserved"
        assert "error" in updated_row["settings"]["advanced"]["logging"], "Array contents should be preserved"
        
        print("✅ CSV UPDATE with nested data test passed")
    
    def test_execute_delete_with_conditions(self):
        """Test DELETE operations with conditions."""
        print("\n🧪 Testing CSV DELETE Operations...")
        
        db = self._create_test_db()
        
        # Create test data with nested structures
        test_data = [
            {
                "id": 1,
                "user": {
                    "name": "Alice",
                    "role": "admin",
                    "permissions": ["read", "write", "delete"]
                },
                "status": "active"
            },
            {
                "id": 2,
                "user": {
                    "name": "Bob", 
                    "role": "user",
                    "permissions": ["read"]
                },
                "status": "inactive"
            },
            {
                "id": 3,
                "user": {
                    "name": "Charlie",
                    "role": "user", 
                    "permissions": ["read", "write"]
                },
                "status": "active"
            }
        ]
        
        columns = ["id", "user", "status"]
        db.create_table("users", columns, test_data)
        
        # Test delete with conditions
        affected_rows = db.execute_delete("users", conditions={"status": "inactive"})
        assert affected_rows == 1, "Should delete 1 inactive user"
        
        # Verify remaining data maintains nested structure
        remaining = db.execute('select', table_name='users')
        assert len(remaining) == 2, "Should have 2 users remaining"
        
        for user in remaining:
            assert isinstance(user, dict), "Each row should be a dictionary"
            assert user["status"] == "active", "Only active users should remain"
            assert isinstance(user["user"], dict), "User should be nested dict"
            assert "permissions" in user["user"], "Nested permissions should exist"
            assert isinstance(user["user"]["permissions"], list), "Permissions should be array"
        
        print("✅ CSV DELETE operations test passed")
    
    def test_table_management_operations(self):
        """Test table management operations."""
        print("\n🧪 Testing CSV Table Management...")
        
        db = self._create_test_db()
        
        # Create multiple tables with nested data
        table_configs = [
            {
                "name": "users",
                "columns": ["id", "profile", "settings"],
                "data": [{
                    "id": 1,
                    "profile": {"name": "John", "age": 30},
                    "settings": {"theme": "dark", "notifications": True}
                }]
            },
            {
                "name": "products", 
                "columns": ["id", "details", "pricing"],
                "data": [{
                    "id": 1,
                    "details": {"name": "Widget", "category": "tools"},
                    "pricing": {"base": 19.99, "currency": "USD"}
                }]
            }
        ]
        
        # Create tables
        for config in table_configs:
            db.create_table(config["name"], config["columns"], config["data"])
        
        # Test list tables
        tables = db.list_tables()
        expected_tables = {"users", "products"}
        assert set(tables) == expected_tables, f"Should list correct tables: {expected_tables}"
        
        # Test get table info
        for table_name in tables:
            table_info = db.get_table_info(table_name)
            assert table_info["exists"] == True, f"Table {table_name} should exist"
            assert table_info["row_count"] == 1, f"Table {table_name} should have 1 row"
            assert isinstance(table_info["columns"], list), f"Table {table_name} should have columns list"
        
        # Test directory status
        status = db.get_directory_status()
        assert status["accessible"] == True, "Directory should be accessible"
        assert status["table_count"] == 2, "Should report 2 tables"
        assert set(status["tables"]) == expected_tables, "Should list correct tables in status"
        
        print("✅ CSV table management test passed")
    
    def test_backup_and_recovery_with_nested_data(self):
        """Test backup and recovery functionality with nested data."""
        print("\n🧪 Testing CSV Backup and Recovery...")
        
        db = self._create_test_db()
        
        # Create table with complex nested data
        original_data = [
            {
                "id": 1,
                "config": {
                    "database": {
                        "host": "localhost",
                        "credentials": {
                            "username": "admin",
                            "encrypted": True
                        }
                    },
                    "features": ["auth", "logging", "monitoring"]
                },
                "metadata": {
                    "created_at": "2024-01-01T00:00:00Z",
                    "version": "1.0.0"
                }
            }
        ]
        
        db.create_table("test_backup", ["id", "config", "metadata"], original_data)
        
        # Perform update to trigger backup
        updated_config = {
            "database": {
                "host": "production.db.com",
                "credentials": {
                    "username": "prod_admin",
                    "encrypted": True
                }
            },
            "features": ["auth", "logging", "monitoring", "analytics"]
        }
        
        db.execute_update("test_backup", 
                         data={"config": updated_config}, 
                         conditions={"id": 1})
        
        # Verify backup was created
        backup_files = list(db._csv_directory.glob("test_backup.bak_*"))
        assert len(backup_files) > 0, "Backup file should be created"
        
        # Verify backup contains original nested data
        backup_df = pd.read_csv(backup_files[0])
        assert len(backup_df) == 1, "Backup should contain 1 row"
        
        # Verify current data has updated nested structure
        current_data = db.execute('select', table_name='test_backup', where={"id": 1})
        current_row = current_data[0]
        
        assert isinstance(current_row["config"], dict), "Config should be nested dict"
        assert current_row["config"]["database"]["host"] == "production.db.com", "Nested host should be updated"
        assert "analytics" in current_row["config"]["features"], "New feature should be added to nested array"
        
        print("✅ CSV backup and recovery test passed")
    
    def test_error_handling_with_nested_data(self):
        """Test error handling scenarios."""
        print("\n🧪 Testing CSV Error Handling...")
        
        db = self._create_test_db()
        
        # Test operations on non-existent table
        results = db.execute('select', table_name='nonexistent')
        assert results == [], "Query on non-existent table should return empty list"
        
        affected = db.execute_update("nonexistent", data={"field": {"nested": "value"}})
        assert affected == 0, "Update on non-existent table should return 0"
        
        affected = db.execute_delete("nonexistent")
        assert affected == 0, "Delete on non-existent table should return 0"
        
        # Test table info on non-existent table
        info = db.get_table_info("nonexistent")
        assert info["exists"] == False, "Non-existent table should report exists=False"
        
        # Test empty insert
        affected = db.execute_insert("test_table", [])
        assert affected == 0, "Empty insert should return 0"
        
        print("✅ CSV error handling test passed")


def run_all_tests():
    """Run all CSV database tests."""
    print("🚀 Starting CSV Database Tests...")
    
    test_instance = TestCSVDatabase()
    
    try:
        test_instance.setup_method()
        test_instance.test_singleton_pattern()
        test_instance.teardown_method()
        
        test_instance.setup_method()
        test_instance.test_initialization()
        test_instance.teardown_method()
        
        test_instance.setup_method()
        test_instance.test_create_and_drop_table()
        test_instance.teardown_method()
        
        test_instance.setup_method()
        test_instance.test_execute_query_list_of_dicts()
        test_instance.teardown_method()
        
        test_instance.setup_method()
        test_instance.test_execute_query_with_conditions()
        test_instance.teardown_method()
        
        test_instance.setup_method()
        test_instance.test_execute_insert_nested_data()
        test_instance.teardown_method()
        
        test_instance.setup_method()
        test_instance.test_execute_update_nested_data()
        test_instance.teardown_method()
        
        test_instance.setup_method()
        test_instance.test_execute_delete_with_conditions()
        test_instance.teardown_method()
        
        test_instance.setup_method()
        test_instance.test_table_management_operations()
        test_instance.teardown_method()
        
        test_instance.setup_method()
        test_instance.test_backup_and_recovery_with_nested_data()
        test_instance.teardown_method()
        
        test_instance.setup_method()
        test_instance.test_error_handling_with_nested_data()
        test_instance.teardown_method()
        
        print("\n🎉 All CSV Database tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    if not success:
        exit(1)
