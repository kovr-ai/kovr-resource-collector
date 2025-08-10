"""Tests for CSV Database operations."""
import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import pandas as pd

# Import the CSV database class
from con_mon.utils.csv_db import CSVDatabase, get_csv_db


def setup_test_environment():
    """Set up a temporary test environment for CSV database tests."""
    # Create a temporary directory for testing
    test_dir = tempfile.mkdtemp()
    test_csv_dir = Path(test_dir) / "data" / "csv"
    test_csv_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a test CSV database instance with custom directory
    test_db = CSVDatabase()
    test_db._csv_directory = test_csv_dir
    
    return test_db, test_dir


def cleanup_test_environment(test_dir):
    """Clean up the test environment."""
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)


def test_csv_database_singleton():
    """Test that CSVDatabase follows singleton pattern."""
    print("\n🧪 Testing CSV Database Singleton Pattern...")
    
    # Create multiple instances
    db1 = CSVDatabase()
    db2 = CSVDatabase()
    db3 = get_csv_db()
    
    # Verify they are all the same instance
    assert db1 is db2, "CSVDatabase should follow singleton pattern"
    assert db1 is db3, "get_csv_db() should return the same singleton instance"
    assert db2 is db3, "All instances should be identical"
    
    print("✅ Singleton pattern test passed")


def test_csv_database_initialization():
    """Test CSV database initialization and directory setup."""
    print("\n🧪 Testing CSV Database Initialization...")
    
    test_db, test_dir = setup_test_environment()
    
    try:
        # Test directory initialization
        assert test_db._csv_directory is not None, "CSV directory should be initialized"
        assert test_db._csv_directory.exists(), "CSV directory should exist"
        assert test_db._initialized == True, "Database should be marked as initialized"
        
        # Test connection
        connection_status = test_db.test_connection()
        assert connection_status == True, "Connection test should pass"
        
        print("✅ Initialization test passed")
        
    finally:
        cleanup_test_environment(test_dir)


def test_create_and_drop_table():
    """Test creating and dropping CSV tables."""
    print("\n🧪 Testing Table Creation and Deletion...")
    
    test_db, test_dir = setup_test_environment()
    
    try:
        # Test create table
        columns = ["id", "name", "email", "age"]
        result = test_db.create_table("users", columns)
        assert result == True, "Table creation should succeed"
        
        # Verify table exists
        assert test_db._table_exists("users"), "Table should exist after creation"
        
        # Test table info
        table_info = test_db.get_table_info("users")
        assert table_info["exists"] == True, "Table should be reported as existing"
        assert table_info["row_count"] == 0, "New table should have 0 rows"
        assert table_info["columns"] == columns, "Table should have correct columns"
        
        # Test create table with initial data
        initial_data = [
            {"id": 1, "name": "John Doe", "email": "john@example.com", "age": 30},
            {"id": 2, "name": "Jane Smith", "email": "jane@example.com", "age": 25}
        ]
        result = test_db.create_table("employees", columns, initial_data)
        assert result == True, "Table creation with data should succeed"
        
        # Verify initial data
        table_info = test_db.get_table_info("employees")
        assert table_info["row_count"] == 2, "Table should have 2 initial rows"
        
        # Test creating duplicate table
        result = test_db.create_table("users", columns)
        assert result == False, "Creating duplicate table should fail"
        
        # Test drop table
        result = test_db.drop_table("users")
        assert result == True, "Table deletion should succeed"
        assert not test_db._table_exists("users"), "Table should not exist after deletion"
        
        # Test dropping non-existent table
        result = test_db.drop_table("nonexistent")
        assert result == False, "Dropping non-existent table should return False"
        
        print("✅ Table creation and deletion tests passed")
        
    finally:
        cleanup_test_environment(test_dir)


def test_insert_operations():
    """Test INSERT operations on CSV tables."""
    print("\n🧪 Testing INSERT Operations...")
    
    test_db, test_dir = setup_test_environment()
    
    try:
        # Create test table
        columns = ["id", "name", "email", "status"]
        test_db.create_table("test_users", columns)
        
        # Test single row insert
        single_row = {"id": 1, "name": "Alice", "email": "alice@example.com", "status": "active"}
        rows_inserted = test_db.execute_insert("test_users", single_row)
        assert rows_inserted == 1, "Should insert 1 row"
        
        # Verify insert
        table_info = test_db.get_table_info("test_users")
        assert table_info["row_count"] == 1, "Table should have 1 row after insert"
        
        # Test multiple rows insert
        multiple_rows = [
            {"id": 2, "name": "Bob", "email": "bob@example.com", "status": "active"},
            {"id": 3, "name": "Charlie", "email": "charlie@example.com", "status": "inactive"}
        ]
        rows_inserted = test_db.execute_insert("test_users", multiple_rows)
        assert rows_inserted == 2, "Should insert 2 rows"
        
        # Verify total rows
        table_info = test_db.get_table_info("test_users")
        assert table_info["row_count"] == 3, "Table should have 3 rows total"
        
        # Test insert with new column
        new_row = {"id": 4, "name": "David", "email": "david@example.com", "status": "active", "department": "IT"}
        rows_inserted = test_db.execute_insert("test_users", new_row)
        assert rows_inserted == 1, "Should insert 1 row with new column"
        
        # Verify new column was added
        table_info = test_db.get_table_info("test_users")
        assert "department" in table_info["columns"], "New column should be added"
        assert table_info["row_count"] == 4, "Table should have 4 rows total"
        
        # Test insert into non-existent table (should create it)
        new_table_data = {"product_id": 1, "product_name": "Widget", "price": 19.99}
        rows_inserted = test_db.execute_insert("products", new_table_data)
        assert rows_inserted == 1, "Should create table and insert row"
        assert test_db._table_exists("products"), "New table should be created"
        
        print("✅ INSERT operations tests passed")
        
    finally:
        cleanup_test_environment(test_dir)


def test_query_operations():
    """Test SELECT/query operations on CSV tables."""
    print("\n🧪 Testing Query Operations...")
    
    test_db, test_dir = setup_test_environment()
    
    try:
        # Create test table with data
        test_data = [
            {"id": 1, "name": "Alice", "department": "IT", "salary": 70000, "status": "active"},
            {"id": 2, "name": "Bob", "department": "HR", "salary": 60000, "status": "active"},
            {"id": 3, "name": "Charlie", "department": "IT", "salary": 80000, "status": "inactive"},
            {"id": 4, "name": "David", "department": "Finance", "salary": 75000, "status": "active"},
            {"id": 5, "name": "Eve", "department": "IT", "salary": 85000, "status": "active"}
        ]
        
        columns = ["id", "name", "department", "salary", "status"]
        test_db.create_table("employees", columns, test_data)
        
        # Test query all rows
        all_results = test_db.execute_query("employees")
        assert len(all_results) == 5, "Should return all 5 rows"
        assert all_results[0]["name"] == "Alice", "First row should be Alice"
        
        # Test query with conditions
        it_employees = test_db.execute_query("employees", conditions={"department": "IT"})
        assert len(it_employees) == 3, "Should return 3 IT employees"
        
        # Test query with multiple conditions
        active_it = test_db.execute_query("employees", conditions={"department": "IT", "status": "active"})
        assert len(active_it) == 2, "Should return 2 active IT employees"
        
        # Test query with specific columns
        names_only = test_db.execute_query("employees", columns=["name"])
        assert len(names_only) == 5, "Should return all 5 rows"
        assert list(names_only[0].keys()) == ["name"], "Should only return name column"
        
        # Test query with conditions and specific columns
        it_names = test_db.execute_query("employees", 
                                       conditions={"department": "IT"}, 
                                       columns=["name", "salary"])
        assert len(it_names) == 3, "Should return 3 IT employees"
        assert set(it_names[0].keys()) == {"name", "salary"}, "Should only return name and salary columns"
        
        # Test wildcard matching
        a_names = test_db.execute_query("employees", conditions={"name": "A*"})
        assert len(a_names) == 1, "Should return 1 employee with name starting with 'A'"
        assert a_names[0]["name"] == "Alice", "Should return Alice"
        
        # Test query on non-existent table
        no_results = test_db.execute_query("nonexistent")
        assert len(no_results) == 0, "Should return empty list for non-existent table"
        
        print("✅ Query operations tests passed")
        
    finally:
        cleanup_test_environment(test_dir)


def test_update_operations():
    """Test UPDATE operations on CSV tables."""
    print("\n🧪 Testing UPDATE Operations...")
    
    test_db, test_dir = setup_test_environment()
    
    try:
        # Create test table with data
        test_data = [
            {"id": 1, "name": "Alice", "department": "IT", "salary": 70000, "status": "active"},
            {"id": 2, "name": "Bob", "department": "HR", "salary": 60000, "status": "active"},
            {"id": 3, "name": "Charlie", "department": "IT", "salary": 80000, "status": "inactive"}
        ]
        
        columns = ["id", "name", "department", "salary", "status"]
        test_db.create_table("employees", columns, test_data)
        
        # Test update single row
        affected_rows = test_db.execute_update("employees", 
                                             data={"salary": 75000}, 
                                             conditions={"id": 1})
        assert affected_rows == 1, "Should update 1 row"
        
        # Verify update
        alice = test_db.execute_query("employees", conditions={"id": 1})
        assert alice[0]["salary"] == 75000, "Alice's salary should be updated"
        
        # Test update multiple rows
        affected_rows = test_db.execute_update("employees", 
                                             data={"status": "promoted"}, 
                                             conditions={"department": "IT"})
        assert affected_rows == 2, "Should update 2 IT employees"
        
        # Verify multiple updates
        it_employees = test_db.execute_query("employees", conditions={"department": "IT"})
        for emp in it_employees:
            assert emp["status"] == "promoted", f"{emp['name']} should have promoted status"
        
        # Test update with wildcard
        affected_rows = test_db.execute_update("employees", 
                                             data={"department": "Engineering"}, 
                                             conditions={"name": "A*"})
        assert affected_rows == 1, "Should update 1 employee with name starting with 'A'"
        
        # Test update all rows (no conditions)
        affected_rows = test_db.execute_update("employees", data={"company": "TechCorp"})
        assert affected_rows == 3, "Should update all 3 employees"
        
        # Verify all rows updated
        all_employees = test_db.execute_query("employees")
        for emp in all_employees:
            assert emp["company"] == "TechCorp", f"{emp['name']} should have company set"
        
        # Test update on non-existent table
        affected_rows = test_db.execute_update("nonexistent", data={"field": "value"})
        assert affected_rows == 0, "Should return 0 for non-existent table"
        
        print("✅ UPDATE operations tests passed")
        
    finally:
        cleanup_test_environment(test_dir)


def test_delete_operations():
    """Test DELETE operations on CSV tables."""
    print("\n🧪 Testing DELETE Operations...")
    
    test_db, test_dir = setup_test_environment()
    
    try:
        # Create test table with data
        test_data = [
            {"id": 1, "name": "Alice", "department": "IT", "status": "active"},
            {"id": 2, "name": "Bob", "department": "HR", "status": "active"},
            {"id": 3, "name": "Charlie", "department": "IT", "status": "inactive"},
            {"id": 4, "name": "David", "department": "Finance", "status": "active"},
            {"id": 5, "name": "Eve", "department": "IT", "status": "inactive"}
        ]
        
        columns = ["id", "name", "department", "status"]
        test_db.create_table("employees", columns, test_data)
        
        # Test delete single row
        affected_rows = test_db.execute_delete("employees", conditions={"id": 1})
        assert affected_rows == 1, "Should delete 1 row"
        
        # Verify deletion
        remaining = test_db.execute_query("employees")
        assert len(remaining) == 4, "Should have 4 rows remaining"
        alice_results = test_db.execute_query("employees", conditions={"id": 1})
        assert len(alice_results) == 0, "Alice should be deleted"
        
        # Test delete multiple rows
        affected_rows = test_db.execute_delete("employees", conditions={"status": "inactive"})
        assert affected_rows == 2, "Should delete 2 inactive employees"
        
        # Verify multiple deletions
        remaining = test_db.execute_query("employees")
        assert len(remaining) == 2, "Should have 2 rows remaining"
        for emp in remaining:
            assert emp["status"] == "active", "Only active employees should remain"
        
        # Test delete with wildcard
        affected_rows = test_db.execute_delete("employees", conditions={"name": "B*"})
        assert affected_rows == 1, "Should delete 1 employee with name starting with 'B'"
        
        # Test delete all rows (no conditions)
        affected_rows = test_db.execute_delete("employees")
        assert affected_rows == 1, "Should delete remaining row"
        
        # Verify table is empty
        remaining = test_db.execute_query("employees")
        assert len(remaining) == 0, "Table should be empty"
        
        # Test delete on non-existent table
        affected_rows = test_db.execute_delete("nonexistent")
        assert affected_rows == 0, "Should return 0 for non-existent table"
        
        print("✅ DELETE operations tests passed")
        
    finally:
        cleanup_test_environment(test_dir)


def test_table_management():
    """Test table management operations."""
    print("\n🧪 Testing Table Management...")
    
    test_db, test_dir = setup_test_environment()
    
    try:
        # Create multiple test tables
        test_db.create_table("users", ["id", "name"])
        test_db.create_table("products", ["id", "name", "price"])
        test_db.create_table("orders", ["id", "user_id", "product_id"])
        
        # Test list tables
        tables = test_db.list_tables()
        expected_tables = {"users", "products", "orders"}
        assert set(tables) == expected_tables, f"Should list correct tables: {expected_tables}"
        
        # Test get table info for each table
        for table_name in tables:
            table_info = test_db.get_table_info(table_name)
            assert table_info["exists"] == True, f"Table {table_name} should exist"
            assert table_info["row_count"] == 0, f"Table {table_name} should be empty"
            assert isinstance(table_info["columns"], list), f"Table {table_name} should have columns list"
            assert table_info["size_bytes"] > 0, f"Table {table_name} should have file size"
            assert "modified_time" in table_info, f"Table {table_name} should have modified time"
        
        # Test get directory status
        status = test_db.get_directory_status()
        assert status["accessible"] == True, "Directory should be accessible"
        assert status["table_count"] == 3, "Should report 3 tables"
        assert set(status["tables"]) == expected_tables, "Should list correct tables in status"
        
        # Add some data and test backup functionality
        test_data = [{"id": 1, "name": "Test User"}]
        test_db.execute_insert("users", test_data)
        
        # Update to trigger backup
        test_db.execute_update("users", data={"name": "Updated User"}, conditions={"id": 1})
        
        # Check for backup files
        backup_files = list(test_db._csv_directory.glob("*.bak_*"))
        assert len(backup_files) > 0, "Should create backup files during updates"
        
        print("✅ Table management tests passed")
        
    finally:
        cleanup_test_environment(test_dir)


def test_error_handling():
    """Test error handling and edge cases."""
    print("\n🧪 Testing Error Handling...")
    
    test_db, test_dir = setup_test_environment()
    
    try:
        # Test operations on non-existent table
        results = test_db.execute_query("nonexistent")
        assert results == [], "Query on non-existent table should return empty list"
        
        affected = test_db.execute_update("nonexistent", data={"field": "value"})
        assert affected == 0, "Update on non-existent table should return 0"
        
        affected = test_db.execute_delete("nonexistent")
        assert affected == 0, "Delete on non-existent table should return 0"
        
        # Test table info on non-existent table
        info = test_db.get_table_info("nonexistent")
        assert info["exists"] == False, "Non-existent table should report exists=False"
        
        # Test empty insert
        affected = test_db.execute_insert("test_table", [])
        assert affected == 0, "Empty insert should return 0"
        
        # Test insert with None data
        affected = test_db.execute_insert("test_table", None)
        assert affected == 0, "None insert should return 0"
        
        print("✅ Error handling tests passed")
        
    finally:
        cleanup_test_environment(test_dir)


def test_backup_and_recovery():
    """Test backup and recovery functionality."""
    print("\n🧪 Testing Backup and Recovery...")
    
    test_db, test_dir = setup_test_environment()
    
    try:
        # Create test table with data
        original_data = [
            {"id": 1, "name": "Alice", "value": 100},
            {"id": 2, "name": "Bob", "value": 200}
        ]
        test_db.create_table("test_backup", ["id", "name", "value"], original_data)
        
        # Perform an update that will create a backup
        test_db.execute_update("test_backup", data={"value": 150}, conditions={"id": 1})
        
        # Check that backup was created
        backup_files = list(test_db._csv_directory.glob("test_backup.bak_*"))
        assert len(backup_files) > 0, "Backup file should be created"
        
        # Verify backup contains original data
        backup_df = pd.read_csv(backup_files[0])
        assert len(backup_df) == 2, "Backup should contain original 2 rows"
        alice_backup = backup_df[backup_df['id'] == 1].iloc[0]
        assert alice_backup['value'] == 100, "Backup should contain original Alice value"
        
        # Verify current data is updated
        current_data = test_db.execute_query("test_backup", conditions={"id": 1})
        assert current_data[0]["value"] == 150, "Current data should be updated"
        
        # Test backup cleanup by creating multiple backups
        for i in range(10):
            test_db.execute_update("test_backup", data={"value": 150 + i}, conditions={"id": 1})
        
        # Check that old backups are cleaned up (should keep only 5)
        backup_files = list(test_db._csv_directory.glob("test_backup.bak_*"))
        assert len(backup_files) <= 5, f"Should keep only 5 backups, found {len(backup_files)}"
        
        print("✅ Backup and recovery tests passed")
        
    finally:
        cleanup_test_environment(test_dir)


def run_all_tests():
    """Run all CSV database tests."""
    print("🚀 Starting CSV Database Tests...")
    
    try:
        test_csv_database_singleton()
        test_csv_database_initialization()
        test_create_and_drop_table()
        test_insert_operations()
        test_query_operations()
        test_update_operations()
        test_delete_operations()
        test_table_management()
        test_error_handling()
        test_backup_and_recovery()
        
        print("\n🎉 All CSV Database tests passed successfully!")
        return True
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n💥 Unexpected error during testing: {e}")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    if not success:
        exit(1) 