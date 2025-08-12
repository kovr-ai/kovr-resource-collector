"""
Check results data loaders for con_mon_results and con_mon_results_history tables.
"""

from typing import List, Optional
from .base import BaseLoader
from con_mon_v2.compliance.models.con_mon_result import ConMonResult, ConMonResultHistory


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
        
        raw_rows = self.db.execute_query(query, (customer_id, connection_id))
        
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
        
        raw_rows = self.db.execute_query(query, (check_id,))
        
        instances = []
        for raw_row in raw_rows:
            processed_row = self.process_row(raw_row)
            instance = ConMonResult.from_row(processed_row)
            instances.append(instance)
        
        print(f"✅ Loaded {len(instances)} ConMonResult for check {check_id}")
        return instances

    def insert_rows(self, instances: List[ConMonResult]) -> int:
        # TODO: implement insert rows
        # delete by check, connection and customer id
        # call super to insert_rows as per BaseLoader logic
        pass


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
        
        raw_rows = self.db.execute_query(query, (customer_id, connection_id))
        
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
        
        raw_rows = self.db.execute_query(query, (check_id,))
        
        instances = []
        for raw_row in raw_rows:
            processed_row = self.process_row(raw_row)
            instance = ConMonResultHistory.from_row(processed_row)
            instances.append(instance)
        
        print(f"✅ Loaded {len(instances)} ConMonResultHistory for check {check_id}")
        return instances 