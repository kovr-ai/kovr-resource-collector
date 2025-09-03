"""
Check results data loaders for con_mon_results and con_mon_results_history tables.
"""

from typing import List, Optional
from .base import BaseLoader
from con_mon.compliance.models.con_mon_result import ConMonResult, ConMonResultHistory
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
        raw_rows = self.db.execute('select', table_name=self.get_table_name, where={'customer_id': customer_id, 'connection_id': connection_id})
        
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
        raw_rows = self.db.execute('select', table_name=self.get_table_name, where={'check_id': check_id})
        
        instances = []
        for raw_row in raw_rows:
            processed_row = self.process_row(raw_row)
            instance = ConMonResult.from_row(processed_row)
            instances.append(instance)
        
        print(f"✅ Loaded {len(instances)} ConMonResult for check {check_id}")
        return instances

    def insert_results(self, instances: List[ConMonResult]) -> int:
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
        total_inserted = history_loader.insert_history(instances)

        # for instance in instances:
        #     self.upsert_row(
        #         ['customer_id', 'connection_id', 'check_id'],
        #         instance
        #     )
        self.delete_insert_rows(
            ['customer_id', 'connection_id', 'check_id'],
            instances
        )

        return total_inserted


class ConMonResultHistoryLoader(BaseLoader):
    """
    Data loader for ConMonResultHistory (con_mon_results_history table).
    Handles historical check results with JSONB fields.
    """

    def __init__(self):
        """Initialize the ConMonResultHistoryLoader with the ConMonResultHistory model."""
        super().__init__(ConMonResultHistory)

    def load_by_customer_and_connection(self, customer_id: str, connection_id: int) -> List[ConMonResultHistory]:
        """
        Load historical check results for a specific customer and connection.
        
        Args:
            customer_id: Customer ID to filter by
            connection_id: Connection ID to filter by
            limit: Maximum number of records to return (optional)
            
        Returns:
            List of ConMonResultHistory for the customer and connection
        """
        raw_rows = self.db.execute('select', table_name='con_mon_results_history', where={'customer_id': customer_id, 'connection_id': connection_id})
        
        instances = []
        for raw_row in raw_rows:
            processed_row = self.process_row(raw_row)
            instance = ConMonResultHistory.from_row(processed_row)
            instances.append(instance)
        
        print(f"✅ Loaded {len(instances)} ConMonResultHistory for customer {customer_id}, connection {connection_id}")
        return instances

    def insert_history(self, instances: List[ConMonResult]) -> int:
        history_records = list()
        for instance in instances:
            history_record = ConMonResultHistory(
                customer_id=instance.customer_id,
                connection_id=instance.connection_id,
                check_id=instance.check_id,
                result=instance.result,
                result_message=instance.result_message,
                success_count=instance.success_count,
                failure_count=instance.failure_count,
                success_percentage=instance.success_percentage,
                success_resources=instance.success_resources,
                failed_resources=instance.failed_resources,
                exclusions=instance.exclusions,
                resource_json=instance.resource_json,
                created_at=instance.created_at,
                updated_at=datetime.now()
            )
            history_records.append(history_record)

        return self.insert_rows(history_records)
