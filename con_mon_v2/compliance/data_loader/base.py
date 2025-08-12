"""
Base data loader class for database operations.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Type, Optional
from pathlib import Path
from con_mon_v2.utils.db import get_db
from con_mon_v2.compliance.models.base import TableModel


class BaseLoader(ABC):
    """
    Abstract base class for compliance data loaders.
    Handles database connections and common row processing.
    """

    def __init__(
        self,
        model: Type[TableModel],
    ):
        self.model = model
        self.db = get_db()

    @property
    def get_model_class(self) -> Type[TableModel]:
        """Return the model class this loader handles."""
        return self.model

    @property
    def get_table_name(self) -> str:
        """Return the database table name."""
        return self.model.table_name

    @property
    def get_select_fields(self) -> List[str]:
        """Return the list of database fields to select."""
        return list(self.model.model_fields.keys())

    def load_all(self) -> List[TableModel]:
        """
        Load all records from the database table.

        Returns:
            List of model instances
        """
        model_class: Type[TableModel] = self.get_model_class
        table_name: str = self.get_table_name
        select_fields: List[str] = self.get_select_fields

        print(f"🗄️  Loading {model_class.__name__} from database table '{table_name}'...")

        # Build SELECT query
        query = f"SELECT {', '.join(select_fields)} FROM {table_name} ORDER BY id"

        # Execute query and get raw rows
        raw_rows = self.db.execute_query(query)

        # Convert rows to model instances
        instances = []
        for raw_row in raw_rows:
            # Process the row (can be overridden in subclasses)
            processed_row = self.process_row(raw_row)

            # Create model instance using from_row method
            instance = model_class.from_row(processed_row)
            instances.append(instance)

        print(f"✅ Loaded {len(instances)} {model_class.__name__} records from database")
        return instances

    def process_row(self, raw_row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a raw database row before converting to model.
        Can be overridden in subclasses for custom processing.

        Args:
            raw_row: Raw row from database

        Returns:
            Processed row ready for model creation
        """
        # Default: return raw row as-is
        return raw_row

    def load_by_ids(self, ids: List[int]) -> List[TableModel]:
        """
        Load records by their IDs.

        Args:
            ids: List of record IDs to load

        Returns:
            List of model instances
        """
        if not ids:
            return self.load_all()

        model_class: Type[TableModel] = self.get_model_class
        table_name: str = self.get_table_name
        select_fields: List[str] = self.get_select_fields

        print(f"🗄️  Loading {len(ids)} {model_class.__name__} records by IDs...")

        # Build SELECT query with WHERE clause
        ids_str = ', '.join(str(id) for id in ids)
        query = f"SELECT {', '.join(select_fields)} FROM {table_name} WHERE id IN ({ids_str}) ORDER BY id"

        # Execute query and get raw rows
        raw_rows = self.db.execute_query(query)

        # Convert rows to model instances
        instances = []
        for raw_row in raw_rows:
            # Process the row
            processed_row = self.process_row(raw_row)

            # Create model instance
            instance = model_class.from_row(processed_row)
            instances.append(instance)

        print(f"✅ Loaded {len(instances)} {model_class.__name__} records by IDs")
        return instances

    def export_to_csv(
        self,
        where_clause: Optional[str] = None,
    ) -> str:
        """
        Export the loader's table data to CSV format.
        
        Args:
            output_path: Output CSV file path (defaults to data/csv/{table_name}.csv)
            where_clause: Optional WHERE clause to filter data (e.g., "is_deleted = false")
            flatten_jsonb: Whether to flatten JSONB fields for CSV compatibility
            
        Returns:
            Path to the created CSV file
        """
        table_name = self.get_table_name
        model_class = self.get_model_class
        
        # Set default where clause for tables with soft deletes
        if where_clause is None and hasattr(self.model, 'is_deleted'):
            where_clause = "is_deleted = false"
            
        print(f"📤 Exporting {model_class.__name__} data to CSV...")
        
        return self.db.export_table_to_csv(
            table_name=table_name,
            where_clause=where_clause
        )
    
    def import_from_csv(
        self,
        update_existing: bool = True,
        batch_size: int = 100
    ) -> int:
        """
        Import CSV data to the loader's table.
        
        Args:
            csv_path: Path to the CSV file to import
            update_existing: Whether to update existing records (based on ID)
            unflatten_jsonb: Whether to reconstruct JSONB fields from flattened CSV
            batch_size: Number of records to process in each batch
            
        Returns:
            Number of records imported/updated
        """
        table_name = self.get_table_name
        model_class = self.get_model_class
            
        print(f"📥 Importing CSV data to {model_class.__name__} table...")
        
        return self.db.import_csv_to_table(
            table_name=table_name,
            update_existing=update_existing,
            batch_size=batch_size
        )
