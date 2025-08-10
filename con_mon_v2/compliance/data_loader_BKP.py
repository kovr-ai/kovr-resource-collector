"""
Data loader for cybersecurity frameworks - loads data from database and CSV files.
Modern class-based architecture with no backward compatibility.
"""

import csv
import os
from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from con_mon_v2.compliance.models import (
    BaseModel, Framework, Control, Standard, StandardControlMapping, 
    FrameworkWithControls, StandardWithControls, ControlWithStandards
)
from con_mon_v2.utils.db import get_db


class BaseLoader(ABC):
    """
    Abstract base class for compliance data loaders.
    Defines the interface that all data loaders must implement.
    """
    
    def __init__(self):
        self.name = self.__class__.__name__

    @classmethod
    def _load_meta_data(cls, model_class):
        """
        Uses model_class and returns the expected meta data.
        
        Args:
            model_class: Pydantic model class (Framework, Control, etc.)
            
        Returns:
            Tuple of (table_name, field_mapping_dict)
        """
        table_name = model_class.get_table_name()
        
        # Define field mappings for each model type
        field_mappings = {
            'framework': {
                'id': 'id',
                'name': 'name', 
                'version': 'version',
                'description': 'description',
                'created_at': 'created_at',
                'updated_at': 'updated_at',
                'active': 'active'
            },
            'control': {
                'id': 'id',
                'framework_id': 'framework_id',
                'control_id': 'control_name',
                'name': 'control_long_name',
                'description': 'control_text',
                'control_family': 'family_name',
                'implementation_guidance': 'control_discussion',
                'created_at': 'created_at',
                'updated_at': 'updated_at'
            },
            'standard': {
                'id': 'id',
                'name': 'name',
                'description': 'long_description',
                'created_at': 'created_at', 
                'updated_at': 'updated_at',
                'active': 'active'
            },
            'standard_control_mapping': {
                'id': 'id',
                'standard_id': 'standard_id',
                'control_id': 'control_id',
                'notes': 'additional_guidance',
                'created_at': 'created_at',
                'updated_at': 'updated_at'
            }
        }
        
        fields = field_mappings.get(table_name, {})
        return table_name, fields

    def _parse_rows_from_connection(
        self, model_class, table_name, fields, rows
    ):

        # Convert rows to model instances
        instances = []
        # TODO: this piece seems common with CSV too. extract in base class
        for row in rows:
            model_data = self._parse_row_from_connection(
                model_class, table_name, fields, row
            )
            instance = model_class(**model_data)
            instances.append(instance)

        print(f"✅ Loaded {len(instances)} {model_class.__name__} records from {self.name.lower()}")
        return instances

    def _parse_row_from_connection(
        self, model_class, table_name, fields, row
    ):
        # Create model data dict with proper field names
        model_data = {}
        for model_field, db_field in fields.items():
            value = row.get(db_field)

            # Handle special field processing
            if model_field == 'status' and db_field == 'active':
                model_data[model_field] = 'active' if value else 'inactive'
            elif model_field == 'version' and value is not None:
                model_data[model_field] = str(value)
            elif model_field == 'name' and model_class == Control and db_field == 'control_long_name':
                # Use control_long_name if available, fallback to control_name
                model_data[model_field] = value or row.get('control_name', '')
            elif model_field == 'description' and model_class == Control:
                # Combine control_text and control_discussion
                control_text = row.get('control_text', '')
                control_discussion = row.get('control_discussion', '')
                model_data[model_field] = control_text or control_discussion or ''
            elif model_field == 'description' and model_class == Standard:
                # Use long_description, fallback to short_description
                long_desc = row.get('long_description')
                short_desc = row.get('short_description', '')
                model_data[model_field] = long_desc or short_desc
            else:
                model_data[model_field] = value

        # Set default values for fields not in database
        if model_class == Framework:
            model_data.setdefault('issuing_organization', None)
            model_data.setdefault('publication_date', None)
            model_data.setdefault('status', 'active' if row.get('active', True) else 'inactive')
        elif model_class == Control:
            model_data.setdefault('priority', 'medium')
            model_data.setdefault('github_check_required', None)
        elif model_class == Standard:
            model_data.setdefault('version', None)
            model_data.setdefault('issuing_organization', None)
            model_data.setdefault('scope', None)
            model_data.setdefault('status', 'active' if row.get('active', True) else 'inactive')
        elif model_class == StandardControlMapping:
            model_data.setdefault('mapping_type', 'direct')
            model_data.setdefault('compliance_level', None)
        return model_data

    @abstractmethod
    def _load_data_from_connection(self, model_class, table_name: str, fields: Dict[str, str]) -> List[BaseModel]:
        """
        Returns list of objects of model_class.
        
        Args:
            model_class: Pydantic model class
            table_name: Database/CSV table name
            fields: Field mapping dictionary
            
        Returns:
            List of model instances
        """
        raise NotImplementedError()
    
    def _load_data(self, model_class):
        """
        Load data for a specific model class.
        
        Args:
            model_class: Pydantic model class
            
        Returns:
            List of model instances
        """
        table_name, fields = self._load_meta_data(model_class)
        rows = self._load_data_from_connection(model_class, table_name, fields)
        return self._parse_rows_from_connection(model_class, table_name, fields, rows)
    
    def load_frameworks(self) -> List[Framework]:
        """Load frameworks from data source."""
        return self._load_data(Framework)
    
    def load_standards(self) -> List[Standard]:
        """Load standards from data source.""" 
        return self._load_data(Standard)
    
    def load_controls(self) -> List[Control]:
        """Load controls from data source."""
        return self._load_data(Control)
    
    def load_standard_control_mappings(self) -> List[StandardControlMapping]:
        """Load standard-control mappings from data source."""
        return self._load_data(StandardControlMapping)
    
    def list_framework_with_controls(
            self,
            frameworks: List[Framework],
            controls: List[Control],
    ) -> List[FrameworkWithControls]:
        """
        Merge controls into frameworks.
        
        Args:
            frameworks: List of Framework objects
            controls: List of Control objects
            
        Returns:
            List of FrameworkWithControls objects
        """
        frameworks_with_controls = []
        for framework in frameworks:
            framework_controls = [c for c in controls if c.framework_id == framework.id]
            
            framework_with_controls = FrameworkWithControls(
                **framework.dict(),
                controls=framework_controls
            )
            frameworks_with_controls.append(framework_with_controls)
        
        return frameworks_with_controls
    
    def list_controls_and_standards(
            self,
            standards: List[Standard],
            controls: List[Control],
            standard_control_mappings: List[StandardControlMapping],
    ) -> Tuple[List[StandardWithControls], List[ControlWithStandards]]:
        """
        Return tuple of both lists of standards with controls and controls with standards.
        
        Args:
            standards: List of Standard objects
            controls: List of Control objects  
            standard_control_mappings: List of StandardControlMapping objects
            
        Returns:
            Tuple of (standards_with_controls, controls_with_standards)
        """
        # Create standards with controls
        standards_with_controls = []
        for standard in standards:
            # Find controls mapped to this standard
            standard_control_ids = [m.control_id for m in standard_control_mappings if m.standard_id == standard.id]
            standard_controls = [c for c in controls if c.id in standard_control_ids]
            
            standard_with_controls = StandardWithControls(
                **standard.dict(),
                controls=standard_controls
            )
            standards_with_controls.append(standard_with_controls)
        
        # Create controls with standards
        controls_with_standards = []
        for control in controls:
            # Find standards mapped to this control
            control_standard_ids = [m.standard_id for m in standard_control_mappings if m.control_id == control.id]
            control_standards = [s for s in standards if s.id in control_standard_ids]
            
            control_with_standards = ControlWithStandards(
                **control.dict(),
                standards=control_standards
            )
            controls_with_standards.append(control_with_standards)
        
        return standards_with_controls, controls_with_standards
    
    def populate_all_data(self) -> Tuple[List[FrameworkWithControls], List[StandardWithControls], List[ControlWithStandards], List[StandardControlMapping]]:
        """
        Load and organize all compliance data with relationships.
        
        Returns:
            Tuple of (frameworks_with_controls, standards_with_controls, controls_with_standards, mappings)
        """
        print(f"🏗️  **Loading All Compliance Data from {self.name}**")
        print("=" * 60)
        
        # Load base data
        frameworks = self.load_frameworks()
        controls = self.load_controls()
        standards = self.load_standards()
        mappings = self.load_standard_control_mappings()
        
        print(f"📊 Loaded base data:")
        print(f"   • {len(frameworks)} frameworks")
        print(f"   • {len(controls)} controls") 
        print(f"   • {len(standards)} standards")
        print(f"   • {len(mappings)} mappings")
        
        # Create relationships
        frameworks_with_controls = self.list_framework_with_controls(frameworks, controls)
        standards_with_controls, controls_with_standards = self.list_controls_and_standards(
            standards, controls, mappings
        )
        
        print(f"🔗 Created relationships:")
        print(f"   • {len(frameworks_with_controls)} frameworks with controls")
        print(f"   • {len(standards_with_controls)} standards with controls") 
        print(f"   • {len(controls_with_standards)} controls with standards")
        print("✅ All compliance data loaded successfully!")
        
        return frameworks_with_controls, standards_with_controls, controls_with_standards, mappings


class DBLoader(BaseLoader):
    """
    Database-based data loader for compliance data.
    Loads data directly from PostgreSQL database.
    """
    
    def __init__(self):
        super().__init__()
        self.name = "Database"
        self.db = get_db()

    def _load_data_from_connection(self, model_class, table_name: str, fields: Dict[str, str]) -> List[Dict]:
        """
        Load data from database connection.
        
        Args:
            model_class: Pydantic model class
            table_name: Database table name
            fields: Field mapping dictionary
            
        Returns:
            List of model instances
        """
        print(f"🗄️  Loading {model_class.__name__} from database table '{table_name}'...")
        
        # Build SELECT query
        db_fields = list(fields.values())
        query = f"SELECT {', '.join(db_fields)} FROM {table_name} ORDER BY id"
        
        return self.db.execute_query(query)


class CSVLoader(BaseLoader):
    """
    CSV-based data loader for compliance data.
    Loads data from exported CSV files.
    """
    
    def __init__(self, csv_dir: str = "data/csv"):
        super().__init__()
        self.name = "CSV Files"
        self.csv_dir = csv_dir
    
    def _load_data_from_connection(self, model_class, table_name: str, fields: Dict[str, str]) -> List[Dict]:
        """
        Load data from CSV files.
        
        Args:
            model_class: Pydantic model class
            table_name: CSV file name (without .csv extension)
            fields: Field mapping dictionary
            
        Returns:
            List of row dictionaries
        """
        csv_file_path = os.path.join(self.csv_dir, f"{table_name}.csv")
        print(f"📁 Loading {model_class.__name__} from CSV file '{csv_file_path}'...")
        
        if not os.path.exists(csv_file_path):
            raise FileNotFoundError(f"CSV file not found: {csv_file_path}")
        
        rows = []
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            rows = list(csv_reader)
        
        return rows

# Singleton instances for global access
_db_loader = None
_csv_loader = None

def get_db_loader() -> DBLoader:
    """Get or create singleton DBLoader instance."""
    global _db_loader
    if _db_loader is None:
        _db_loader = DBLoader()
    return _db_loader

def get_csv_loader(csv_dir: str = "data/csv") -> CSVLoader:
    """Get or create singleton CSVLoader instance."""
    global _csv_loader
    if _csv_loader is None:
        _csv_loader = CSVLoader(csv_dir)
    return _csv_loader
