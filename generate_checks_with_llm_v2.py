"""Generate and validate checks using LLM."""
from typing import Type, Dict, List
from pydantic import BaseModel
import yaml

from con_mon_v2.compliance import Control, get_csv_loader
from con_mon_v2.checks import Check, get_loaded_checks
from con_mon_v2.resources import ResourceCollection
from con_mon_v2.utils.llm import generate_checks_yaml
from con_mon_v2.checks.models import CheckResultStatement, CheckFailureFix, CheckMetadata, ComparisonOperation, ComparisonOperationEnum
from con_mon_v2.utils.db import get_db
from con_mon_v2.utils.services import ResourceCollectionService


class CheckService(object):
    def __init__(
        self,
        check: Check,
        connector_type: str,
    ):
        self.check = check
        self.connector_type = connector_type
        self.resource_service = ResourceCollectionService(connector_type)

    def get_resource_collection(
        self,
        credentials: dict,
    ):
        return self.resource_service.get_resource_collection(credentials)

    @property
    def resource_type(self) -> Type[BaseModel]:
        return self.check.resource_type

    @property
    def _all_resource_field_paths(self) -> list[str]:
        return self.resource_service._all_resource_field_paths

    def _validate_field_path(
        self,
        field_path: str,
        resource: Resource,
    ) -> str:
        return self.resource_service._validate_field_path(field_path, resource)

    def validate_resource_field_paths(
        self,
        resource_collection: ResourceCollection,
    ) -> dict[str, dict[str, str]]:
        return self.resource_service.validate_resource_field_paths(resource_collection)

    def validate_execute_check_logic(
        self,
        resource_collection: ResourceCollection,
    ) -> str:
        try:
            # Execute the check evaluation
            results = self.check.evaluate(resource_collection.resources)
            
            if not results:
                return "not found"
                
            # Count successes and failures
            success_count = sum(1 for result in results if result)
            total_count = len(results)
            
            if total_count == 0:
                return "not found"
            elif success_count == total_count:
                return "success"
            elif success_count == 0:
                return "failure"
            else:
                return "partial"
                
        except Exception as e:
            return "error"


class ControlService(object):
    def __init__(
        self,
        control: Control,
    ):
        self.control = control

    def get_checks_from_database(self) -> dict[str, Check]:
        """
        Get all checks mapped to this control from the database.
        
        Returns:
            Dictionary mapping connector type to Check object
        """
        db = get_db()
        checks = {}
        
        try:
            # Get all loaded checks
            loaded_checks = get_loaded_checks()
            
            # Get check IDs mapped to this control
            with db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT check_id
                        FROM control_checks_mapping 
                        WHERE control_id = %s AND is_deleted = false;
                    """, (self.control.id,))
                    
                    check_ids = [row[0] for row in cursor.fetchall()]
                    
            # Get checks by their IDs
            for check_id in check_ids:
                for check in loaded_checks.values():
                    if check.id == check_id:
                        # Determine connector type from connection_id
                        connector_type = 'github' if check.connection_id == 1 else 'aws' if check.connection_id == 2 else 'unknown'
                        checks[connector_type] = check
                        break
            
            return checks
            
        except Exception as e:
            print(f"Failed to get checks from database: {str(e)}")
            return {}

    def generate_checks_using_llm(
        self,
    ) -> dict[str, Check]:
        connector_types = ['github', 'aws']
        checks = {}
        
        for connector_type in connector_types:
            try:
                # Generate check configuration using LLM
                check_config = generate_checks_yaml(
                    control_name=self.control.control_id,
                    control_text=self.control.description,
                    control_title=self.control.name,
                    control_id=self.control.id,
                    resource_type=connector_type,
                    connection_id=1  # Default connection ID
                )
                
                # Parse YAML configuration
                config = yaml.safe_load(check_config)
                if not config or 'checks' not in config or not config['checks']:
                    print(f"No valid check configuration generated for {connector_type}")
                    continue
                    
                check_data = config['checks'][0]  # Get first check configuration
                print(f"\nCheck data for {connector_type}:")
                print(yaml.dump(check_data, default_flow_style=False))
                
                # Create output statements from LLM response
                output_statements = check_data.get('output_statements', {})
                if not isinstance(output_statements, dict) or not all(k in output_statements for k in ['success', 'failure']):
                    print(f"Invalid output statements in LLM response for {connector_type}")
                    continue
                
                # If partial is null or missing, use success message with "partially" added
                if 'partial' not in output_statements or output_statements['partial'] is None:
                    output_statements['partial'] = f"{output_statements['success']} (partially)"
                
                output_statements = CheckResultStatement(**output_statements)
                
                # Create fix details
                fix_details = CheckFailureFix(
                    description=check_data.get('fix_details', {}).get('description', 'No fix description provided'),
                    instructions=check_data.get('fix_details', {}).get('instructions', ['No fix instructions provided']),
                    estimated_date=check_data.get('fix_details', {}).get('estimated_date', '2024-12-31'),
                    automation_available=check_data.get('fix_details', {}).get('automation_available', False)
                )
                
                # Create metadata
                metadata = CheckMetadata(
                    tags=check_data.get('tags', []),
                    severity=check_data.get('severity', 'medium'),
                    category=check_data.get('category', 'configuration')
                )
                
                # Create operation
                operation = ComparisonOperation(
                    name=ComparisonOperationEnum.CUSTOM,
                    custom_function=None  # Will be set from custom_logic
                )
                
                # Get resource type class
                from con_mon_v2.resources.models import Resource
                
                # Create a check using the LLM-generated configuration
                check = Check(
                    id=1,  # This should be auto-generated or retrieved from DB
                    connection_id=check_data.get('connection_id', 1),
                    name=check_data.get('name', f"{self.control.name}_{connector_type}"),
                    description=check_data.get('description', f"{self.control.description} for {connector_type}"),
                    field_path=check_data.get('field_path', ''),
                    operation=operation,
                    expected_value=check_data.get('expected_value'),
                    output_statements=output_statements,
                    fix_details=fix_details,
                    metadata=metadata,
                    resource_type=Resource,
                    created_by=check_data.get('created_by', 'test_script'),
                    updated_by=check_data.get('updated_by', 'test_script'),
                )
                
                checks[connector_type] = check
            except Exception as e:
                print(f"Failed to generate check for {connector_type}: {str(e)}")
                continue
                
        return checks


if __name__ == '__main__':
    # fetch controls from CSV
    csv_loader = get_csv_loader()
    controls = csv_loader.load_controls()
    # Use the first control for testing
    control = controls[10]
    control_service = ControlService(control)
    
    print("\nGetting checks from database:")
    db_checks = control_service.get_checks_from_database()
    for connector_type, check in db_checks.items():
        print(f"\nExisting check for {connector_type}:")
        print(f"Name: {check.name}")
        print(f"Description: {check.description}")
        print(f"Field Path: {check.field_path}")
        print(f"Operation: {check.operation.name}")
        print(f"Expected Value: {check.expected_value}")
        print(f"Severity: {check.metadata.severity}")
        print(f"Category: {check.metadata.category}")
        print(f"Tags: {check.metadata.tags}")
        print(f"Output Statements:")
        print(f"  Success: {check.output_statements.success}")
        print(f"  Failure: {check.output_statements.failure}")
        print(f"  Partial: {check.output_statements.partial}")
        print(f"Fix Details:")
        print(f"  Description: {check.fix_details.description}")
        print(f"  Instructions: {check.fix_details.instructions}")
        print(f"  Estimated Date: {check.fix_details.estimated_date}")
        print(f"  Automation Available: {check.fix_details.automation_available}")
        
        # Create check service for validation
        check_service = CheckService(check=check, connector_type=connector_type)
        
        # Get resource collection
        resource_collection = check_service.get_resource_collection(credentials={})
        
        # Validate field paths
        print("\nValidating field paths:")
        field_validation = check_service.validate_resource_field_paths(resource_collection)
        for resource_type, validations in field_validation.items():
            print(f"\nResource type: {resource_type}")
            for field_path, validation_result in validations.items():
                print(f"  {field_path}: {validation_result}")
        
        # Validate check logic
        print("\nValidating check logic:")
        logic_validation = check_service.validate_execute_check_logic(resource_collection)
        print(f"Result: {logic_validation}")
    
    print("\nGenerating new checks using LLM:")
    mapped_checks = control_service.generate_checks_using_llm()
    for connector_type, check in mapped_checks.items():
        print(f"\nGenerated check for {connector_type}:")
        print(f"Name: {check.name}")
        print(f"Description: {check.description}")
        print(f"Field Path: {check.field_path}")
        print(f"Operation: {check.operation.name}")
        print(f"Expected Value: {check.expected_value}")
        print(f"Severity: {check.metadata.severity}")
        print(f"Category: {check.metadata.category}")
        print(f"Tags: {check.metadata.tags}")
        print(f"Output Statements:")
        print(f"  Success: {check.output_statements.success}")
        print(f"  Failure: {check.output_statements.failure}")
        print(f"  Partial: {check.output_statements.partial}")
        print(f"Fix Details:")
        print(f"  Description: {check.fix_details.description}")
        print(f"  Instructions: {check.fix_details.instructions}")
        print(f"  Estimated Date: {check.fix_details.estimated_date}")
        print(f"  Automation Available: {check.fix_details.automation_available}")
        
        # Create check service for validation
        check_service = CheckService(check=check, connector_type=connector_type)
        
        # Get resource collection
        resource_collection = check_service.get_resource_collection(credentials={})
        
        # Validate field paths
        print("\nValidating field paths:")
        field_validation = check_service.validate_resource_field_paths(resource_collection)
        for resource_type, validations in field_validation.items():
            print(f"\nResource type: {resource_type}")
            for field_path, validation_result in validations.items():
                print(f"  {field_path}: {validation_result}")
        
        # Validate check logic
        print("\nValidating check logic:")
        logic_validation = check_service.validate_execute_check_logic(resource_collection)
        print(f"Result: {logic_validation}")

