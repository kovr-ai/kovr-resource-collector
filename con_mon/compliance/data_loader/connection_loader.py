"""
Connection data loader for con_mon.

Provides methods to load Connection objects from the self.db with various
filtering and querying options.
"""
from typing import List, Optional, Dict
from con_mon.resources.models import InfoData
from con_mon.compliance.data_loader.base import BaseLoader
from con_mon.compliance.models.connection import Connection, ConnectionType


class ConnectionLoader(BaseLoader):
    """
    Data loader for Connection objects.
    
    Provides methods to load connections from the self.db with filtering
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
        where = {'customer_id': customer_id}
        if not include_deleted:
            where['is_deleted'] = False
        rows = self.db.execute('select', table_name=self.get_table_name, where=where)
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
        where = {'type': connection_type.value}
        if not include_deleted:
            where['is_deleted'] = False
        rows = self.db.execute('select', table_name=self.get_table_name, where=where)
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
        where = {'customer_id': customer_id, 'type': connection_type.value}
        if not include_deleted:
            where['is_deleted'] = False
        rows = self.db.execute('select', table_name=self.get_table_name, where=where)
        return [Connection(**row) for row in rows]
    
    def load_active_connections(self, customer_id: Optional[str] = None) -> List[Connection]:
        """
        Load only active (non-deleted) connections.
        
        Args:
            customer_id: Optional customer ID to filter by
            
        Returns:
            List of active Connection objects
        """
        where = {'is_deleted': False}
        if customer_id:
            where['customer_id'] = customer_id
        rows = self.db.execute('select', table_name=self.get_table_name, where=where)
        return [Connection(**row) for row in rows]
    
    def load_with_credentials(self, customer_id: Optional[str] = None) -> List[Connection]:
        """
        Load connections that have credentials configured.
        
        Args:
            customer_id: Optional customer ID to filter by
            
        Returns:
            List of Connection objects with credentials
        """
        where = {'is_deleted': False}
        if customer_id:
            where['customer_id'] = customer_id
        rows = self.db.execute('select', table_name=self.get_table_name, where=where)
        # Filter for credentials presence in memory for backend-agnostic behavior
        rows = [r for r in rows if r.get('credentials') not in (None, {}, '')]
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
        where = {'is_deleted': False}
        if customer_id:
            where['customer_id'] = customer_id
        rows = self.db.execute('select', table_name=self.get_table_name, where=where)
        # Filter by synced_at in memory
        from datetime import datetime, timedelta
        cutoff = datetime.now() - timedelta(hours=hours)
        def parse_dt(val):
            if not val:
                return None
            try:
                return datetime.fromisoformat(str(val).replace('Z', '+00:00'))
            except Exception:
                return None
        rows = [r for r in rows if parse_dt(r.get('synced_at')) and parse_dt(r.get('synced_at')) > cutoff]
        return [Connection(**row) for row in rows]
    
    def get_connection_types_summary(self, customer_id: Optional[str] = None) -> Dict[str, int]:
        """
        Get a summary of connection types and their counts.
        
        Args:
            customer_id: Optional customer ID to filter by
            
        Returns:
            Dictionary mapping connection type names to counts
        """
        where = {'is_deleted': False}
        if customer_id:
            where['customer_id'] = customer_id
        rows = self.db.execute('select', table_name=self.get_table_name, where=where)
        
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
        where = {'is_deleted': False}
        if customer_id:
            where['customer_id'] = customer_id
        rows = self.db.execute('select', table_name=self.get_table_name, where=where)
        # Apply search filtering in memory (alias or customer_id contains term)
        term_lower = search_term.lower()
        rows = [r for r in rows if term_lower in str(r.get('alias', '')).lower() or term_lower in str(r.get('customer_id', '')).lower()]
        return [Connection(**row) for row in rows]

    def update_connection_data(
        self,
        connection_id: int,
        info_data: InfoData
    ) -> int:
        """
        Update the 'info' key inside the connection's metadata in a database-agnostic way.

        Uses only the generic db.execute interface so it works with both CSV and PostgreSQL backends.

        Args:
            connection_id: Connection ID to update
            info_data: InfoData payload to set under metadata['info']

        Returns:
            Number of records updated (int)
        """
        # Normalize info payload
        info_dict = info_data.model_dump() if hasattr(info_data, 'model_dump') else dict(info_data or {})

        # Load current metadata using the model's table name
        rows = self.db.execute(
            'select',
            table_name=self.get_table_name,
            select=['metadata'],
            where={'id': connection_id, 'is_deleted': False},
        )

        current_metadata = {}
        if rows:
            existing = rows[0].get('metadata')
            if isinstance(existing, dict):
                current_metadata = existing

        print(f'Current metadata: {current_metadata.keys()}')
        updated_metadata = dict(current_metadata)
        updated_metadata['info'] = info_dict
        print(f'Updated info: {current_metadata['info'].keys()}')

        from datetime import datetime as _dt
        affected = self.db.execute(
            'update',
            table_name=self.get_table_name,
            update={'metadata': updated_metadata, 'updated_at': _dt.now().isoformat()},
            where={'id': connection_id, 'is_deleted': False},
        )

        # Both backends return an int for update via db.execute
        return int(affected or 0)
