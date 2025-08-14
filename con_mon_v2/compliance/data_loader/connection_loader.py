"""
Connection data loader for con_mon_v2.

Provides methods to load Connection objects from the database with various
filtering and querying options.
"""
from typing import List, Optional, Dict, Any
from con_mon_v2.compliance.data_loader.base import BaseLoader
from con_mon_v2.compliance.models.connection import Connection, ConnectionType


class ConnectionLoader(BaseLoader):
    """
    Data loader for Connection objects.
    
    Provides methods to load connections from the database with filtering
    options for customer, connection type, and active status.
    """
    
    def __init__(self):
        """Initialize the connection loader."""
        super().__init__(Connection)
    
    def load_by_customer(self, customer_id: str, include_deleted: bool = False) -> List[Connection]:
        """
        Load connections for a specific customer.
        
        Args:
            customer_id: Customer ID to filter by
            include_deleted: Whether to include soft-deleted connections
            
        Returns:
            List of Connection objects for the customer
        """
        query = f"SELECT * FROM {self.get_table_name} WHERE customer_id = %s"
        params = [customer_id]
        
        if not include_deleted:
            query += " AND is_deleted = %s"
            params.append(False)
            
        query += " ORDER BY id"
        
        rows = self.db.execute_query(query, tuple(params))
        return [Connection(**row) for row in rows]
    
    def load_by_type(self, connection_type: ConnectionType, include_deleted: bool = False) -> List[Connection]:
        """
        Load connections by connection type.
        
        Args:
            connection_type: Connection type to filter by
            include_deleted: Whether to include soft-deleted connections
            
        Returns:
            List of Connection objects of the specified type
        """
        query = f"SELECT * FROM {self.get_table_name} WHERE type = %s"
        params = [connection_type.value]
        
        if not include_deleted:
            query += " AND is_deleted = %s"
            params.append(False)
            
        query += " ORDER BY id"
        
        rows = self.db.execute_query(query, tuple(params))
        return [Connection(**row) for row in rows]
    
    def load_by_customer_and_type(self, customer_id: str, connection_type: ConnectionType, 
                                  include_deleted: bool = False) -> List[Connection]:
        """
        Load connections by customer and connection type.
        
        Args:
            customer_id: Customer ID to filter by
            connection_type: Connection type to filter by
            include_deleted: Whether to include soft-deleted connections
            
        Returns:
            List of Connection objects matching the criteria
        """
        query = f"SELECT * FROM {self.get_table_name} WHERE customer_id = %s AND type = %s"
        params = [customer_id, connection_type.value]
        
        if not include_deleted:
            query += " AND is_deleted = %s"
            params.append(False)
            
        query += " ORDER BY id"
        
        rows = self.db.execute_query(query, tuple(params))
        return [Connection(**row) for row in rows]
    
    def load_active_connections(self, customer_id: Optional[str] = None) -> List[Connection]:
        """
        Load only active (non-deleted) connections.
        
        Args:
            customer_id: Optional customer ID to filter by
            
        Returns:
            List of active Connection objects
        """
        query = f"SELECT * FROM {self.get_table_name} WHERE is_deleted = %s"
        params = [False]
        
        if customer_id:
            query += " AND customer_id = %s"
            params.append(customer_id)
            
        query += " ORDER BY id"
        
        rows = self.db.execute_query(query, tuple(params))
        return [Connection(**row) for row in rows]
    
    def load_with_credentials(self, customer_id: Optional[str] = None) -> List[Connection]:
        """
        Load connections that have credentials configured.
        
        Args:
            customer_id: Optional customer ID to filter by
            
        Returns:
            List of Connection objects with credentials
        """
        query = f"""
            SELECT * FROM {self.get_table_name} 
            WHERE is_deleted = %s 
            AND credentials IS NOT NULL 
            AND credentials != '{{}}'
        """
        params = [False]
        
        if customer_id:
            query += " AND customer_id = %s"
            params.append(customer_id)
            
        query += " ORDER BY id"
        
        rows = self.db.execute_query(query, tuple(params))
        return [Connection(**row) for row in rows]
    
    def load_recently_synced(self, hours: int = 24, customer_id: Optional[str] = None) -> List[Connection]:
        """
        Load connections that were synced recently.
        
        Args:
            hours: Number of hours to look back for recent syncs
            customer_id: Optional customer ID to filter by
            
        Returns:
            List of Connection objects synced within the specified time
        """
        query = f"""
            SELECT * FROM {self.get_table_name} 
            WHERE is_deleted = %s 
            AND synced_at IS NOT NULL 
            AND synced_at > NOW() - INTERVAL '%s hours'
        """
        params = [False, hours]
        
        if customer_id:
            query += " AND customer_id = %s"
            params.append(customer_id)
            
        query += " ORDER BY synced_at DESC"
        
        rows = self.db.execute_query(query, tuple(params))
        return [Connection(**row) for row in rows]
    
    def get_connection_types_summary(self, customer_id: Optional[str] = None) -> Dict[str, int]:
        """
        Get a summary of connection types and their counts.
        
        Args:
            customer_id: Optional customer ID to filter by
            
        Returns:
            Dictionary mapping connection type names to counts
        """
        query = f"""
            SELECT type, COUNT(*) as count 
            FROM {self.get_table_name} 
            WHERE is_deleted = %s
        """
        params = [False]
        
        if customer_id:
            query += " AND customer_id = %s"
            params.append(customer_id)
            
        query += " GROUP BY type ORDER BY count DESC"
        
        rows = self.db.execute_query(query, tuple(params))
        
        # Convert type IDs to names
        summary = {}
        for row in rows:
            try:
                connection_type = ConnectionType(row['type'])
                type_name = connection_type.name.replace('_', ' ').title()
                summary[type_name] = row['count']
            except ValueError:
                # Handle unknown connection types
                summary[f"Unknown Type ({row['type']})"] = row['count']
        
        return summary
    
    def search_connections(self, search_term: str, customer_id: Optional[str] = None) -> List[Connection]:
        """
        Search connections by alias or customer ID.
        
        Args:
            search_term: Term to search for in alias or customer_id
            customer_id: Optional customer ID to filter by
            
        Returns:
            List of Connection objects matching the search term
        """
        query = f"""
            SELECT * FROM {self.get_table_name} 
            WHERE is_deleted = %s 
            AND (alias ILIKE %s OR customer_id ILIKE %s)
        """
        search_pattern = f"%{search_term}%"
        params = [False, search_pattern, search_pattern]
        
        if customer_id:
            query += " AND customer_id = %s"
            params.append(customer_id)
            
        query += " ORDER BY alias, id"
        
        rows = self.db.execute_query(query, tuple(params))
        return [Connection(**row) for row in rows]

    def update_connection_data(self, info_data: dict):
        """
        Update connection metadata with info_data from provider execution.

        This function:
        1. Loads existing connection metadata from database
        2. Updates the 'info' key in metadata with the provided info_data
        3. Saves the updated metadata back to the database

        Args:
            connection_id: ID of the connection to update
            info_data: Dictionary or InfoData object containing provider execution metadata

        The info_data typically contains:
        - Collection statistics (total_resources_collected, etc.)
        - Provider-specific metadata (authenticated_user, rate_limits, etc.)
        - API metadata (collection_time, api_version, etc.)
        """
        # Convert info_data to dict if it's an InfoData object
        if hasattr(info_data, 'to_dict'):
            info_dict = info_data.to_dict()
            print(f"   • Info data type: {type(info_data).__name__} (converted to dict)")
        elif hasattr(info_data, 'model_dump'):
            info_dict = info_data.model_dump()
            print(f"   • Info data type: {type(info_data).__name__} (Pydantic model)")
        elif isinstance(info_data, dict):
            info_dict = info_data
            print(f"   • Info data type: dict")
        else:
            info_dict = dict(info_data) if info_data else {}
            print(f"   • Info data type: {type(info_data).__name__} (converted to dict)")

        print(f"   • Info data keys: {list(info_dict.keys()) if info_dict else 'No info data'}")

        # Step 1: Get current connection metadata
        query_sql = """
        SELECT metadata 
        FROM connections 
        WHERE id = %s AND is_deleted = FALSE;
        """

        results = database.execute_query(query_sql, (connection_id,))

        if not results:
            print(f"❌ Connection ID {connection_id} not found or has been deleted")
            return

        # Step 2: Update metadata with new info
        current_metadata = results[0]['metadata'] or {}
        print(
            f"   • Current metadata keys: {list(current_metadata.keys()) if current_metadata else 'No existing metadata'}")

        # Preserve existing metadata and update 'info' key
        updated_metadata = current_metadata.copy()
        updated_metadata['info'] = info_dict

        # Step 3: Update the connection record
        update_sql = """
        UPDATE connections 
        SET metadata = %s, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s AND is_deleted = FALSE;
        """

        affected_rows = database.execute_update(
            update_sql,
            (safe_json_dumps(updated_metadata), connection_id)
        )

        if affected_rows > 0:
            print(f"✅ **Connection metadata updated successfully:**")
            print(f"   • Rows affected: {affected_rows}")
            print(f"   • Info data stored under 'info' key")
            print(f"   • Existing metadata preserved")
            if info_dict:
                info_summary = []
                for key, value in info_dict.items():
                    if isinstance(value, list):
                        info_summary.append(f"{key}: {len(value)} items")
                    elif isinstance(value, dict):
                        info_summary.append(f"{key}: {len(value)} keys")
                    else:
                        info_summary.append(f"{key}: {value}")
                print(f"   • Info content: {', '.join(info_summary[:5])}{'...' if len(info_summary) > 5 else ''}")
        else:
            print(f"⚠️ No rows were updated for connection ID {connection_id}")

