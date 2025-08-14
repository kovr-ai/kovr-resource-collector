"""
Check results data loaders for con_mon_results and con_mon_results_history tables.
"""

from typing import List, Optional
from .base import BaseLoader
from con_mon_v2.compliance.models.con_mon_result import ConMonResult, ConMonResultHistory
from datetime import datetime


class ConMonResultLoader(BaseLoader):
    """
    Data loader for ConMonResult (con_mon_results table).
    Handles the current/latest check results with JSONB fields.
    """

    def __init__(self):
        """Initialize the ConMonResultLoader with the ConMonResult model."""
        super().__init__(ConMonResult)

    def load_by_customer_and_connection(self, customer_id: str, connection_id: int) -> List[ConMonResult]:
        """
        Load check results for a specific customer and connection.
        
        Args:
            customer_id: Customer ID to filter by
            connection_id: Connection ID to filter by
            
        Returns:
            List of ConMonResult for the customer and connection
        """
        table_name = self.get_table_name
        select_fields = self.get_select_fields
        
        query = f"""
        SELECT {', '.join(select_fields)} 
        FROM {table_name} 
        WHERE customer_id = %s AND connection_id = %s 
        ORDER BY created_at DESC
        """
        
        raw_rows = self.db.execute('select', table_name='con_mon_results', where={'customer_id': customer_id, 'connection_id': connection_id})
        
        instances = []
        for raw_row in raw_rows:
            processed_row = self.process_row(raw_row)
            instance = ConMonResult.from_row(processed_row)
            instances.append(instance)
        
        print(f"✅ Loaded {len(instances)} ConMonResult for customer {customer_id}, connection {connection_id}")
        return instances

    def load_by_check_id(self, check_id: str) -> List[ConMonResult]:
        """
        Load check results for a specific check ID across all customers/connections.
        
        Args:
            check_id: Check ID to filter by
            
        Returns:
            List of ConMonResult for the check
        """
        table_name = self.get_table_name
        select_fields = self.get_select_fields
        
        query = f"""
        SELECT {', '.join(select_fields)} 
        FROM {table_name} 
        WHERE check_id = %s 
        ORDER BY created_at DESC
        """
        
        raw_rows = self.db.execute('select', table_name='con_mon_results', where={'check_id': check_id})
        
        instances = []
        for raw_row in raw_rows:
            processed_row = self.process_row(raw_row)
            instance = ConMonResult.from_row(processed_row)
            instances.append(instance)
        
        print(f"✅ Loaded {len(instances)} ConMonResult for check {check_id}")
        return instances

    def insert_rows(self, instances: List[ConMonResult]) -> int:
        """
        Insert ConMonResult instances with history management.
        
        This method:
        1. Loads existing records for the same customer/connection/check combinations
        2. Moves existing records to history table
        3. Inserts new records
        
        Args:
            instances: List of ConMonResult instances to insert
            
        Returns:
            Number of records successfully inserted
        """
        if not instances:
            return 0
            
        print(f"💾 Inserting {len(instances)} ConMonResult records with history management...")
        
        # Initialize history loader
        history_loader = ConMonResultHistoryLoader()
        
        total_inserted = 0
        total_archived = 0
        
        try:
            for instance in instances:
                # Load existing records for this customer/connection/check combination
                existing_records = self.load_by_customer_and_connection(
                    instance.customer_id, 
                    instance.connection_id
                )
                
                # Filter to just this specific check
                existing_for_check = [
                    record for record in existing_records 
                    if record.check_id == instance.check_id
                ]
                
                # Move existing records to history
                if existing_for_check:
                    print(f"   📜 Moving {len(existing_for_check)} existing records to history for check {instance.check_id}...")
                    
                    history_records = []
                    for existing_record in existing_for_check:
                        # Create history record from existing record
                        history_record = ConMonResultHistory(
                            customer_id=existing_record.customer_id,
                            connection_id=existing_record.connection_id,
                            check_id=existing_record.check_id,
                            result=existing_record.result,
                            result_message=existing_record.result_message,
                            success_count=existing_record.success_count,
                            failure_count=existing_record.failure_count,
                            success_percentage=existing_record.success_percentage,
                            success_resources=existing_record.success_resources,
                            failed_resources=existing_record.failed_resources,
                            exclusions=existing_record.exclusions,
                            resource_json=existing_record.resource_json,
                            created_at=existing_record.created_at,
                            updated_at=datetime.now()
                        )
                        history_records.append(history_record)
                    
                    # Insert into history table
                    archived_count = history_loader.insert_rows(history_records)
                    total_archived += archived_count
                    print(f"      ✅ Archived {archived_count} records to history")
                
                # Insert the new record using parent class method
                inserted_count = super().insert_rows([instance])
                total_inserted += inserted_count
                print(f"   💾 Inserted new record for check {instance.check_id}")
            
            print(f"   📊 History management completed:")
            print(f"      • New records inserted: {total_inserted}")
            print(f"      • Records archived to history: {total_archived}")
            
            return total_inserted
            
        except Exception as e:
            print(f"   ❌ Insert with history management failed: {e}")
            raise


class ConMonResultHistoryLoader(BaseLoader):
    """
    Data loader for ConMonResultHistory (con_mon_results_history table).
    Handles historical check results with JSONB fields.
    """

    def __init__(self):
        """Initialize the ConMonResultHistoryLoader with the ConMonResultHistory model."""
        super().__init__(ConMonResultHistory)

    def load_by_customer_and_connection(self, customer_id: str, connection_id: int, 
                                       limit: Optional[int] = None) -> List[ConMonResultHistory]:
        """
        Load historical check results for a specific customer and connection.
        
        Args:
            customer_id: Customer ID to filter by
            connection_id: Connection ID to filter by
            limit: Maximum number of records to return (optional)
            
        Returns:
            List of ConMonResultHistory for the customer and connection
        """
        table_name = self.get_table_name
        select_fields = self.get_select_fields
        
        query = f"""
        SELECT {', '.join(select_fields)} 
        FROM {table_name} 
        WHERE customer_id = %s AND connection_id = %s 
        ORDER BY archived_at DESC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        raw_rows = self.db.execute('select', table_name='con_mon_results_history', where={'customer_id': customer_id, 'connection_id': connection_id})
        
        instances = []
        for raw_row in raw_rows:
            processed_row = self.process_row(raw_row)
            instance = ConMonResultHistory.from_row(processed_row)
            instances.append(instance)
        
        print(f"✅ Loaded {len(instances)} ConMonResultHistory for customer {customer_id}, connection {connection_id}")
        return instances

    def load_by_check_id_with_history(self, check_id: str, 
                                     limit: Optional[int] = None) -> List[ConMonResultHistory]:
        """
        Load historical check results for a specific check ID.
        
        Args:
            check_id: Check ID to filter by
            limit: Maximum number of records to return (optional)
            
        Returns:
            List of ConMonResultHistory for the check
        """
        table_name = self.get_table_name
        select_fields = self.get_select_fields
        
        query = f"""
        SELECT {', '.join(select_fields)} 
        FROM {table_name} 
        WHERE check_id = %s 
        ORDER BY archived_at DESC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        raw_rows = self.db.execute('select', table_name='con_mon_results_history', where={'check_id': check_id})
        
        instances = []
        for raw_row in raw_rows:
            processed_row = self.process_row(raw_row)
            instance = ConMonResultHistory.from_row(processed_row)
            instances.append(instance)
        
        print(f"✅ Loaded {len(instances)} ConMonResultHistory for check {check_id}")
        return instances 