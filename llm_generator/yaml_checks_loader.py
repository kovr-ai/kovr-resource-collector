import os
import glob
import yaml
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
from con_mon.compliance.models import (
    Check,
    CheckMetadata,
    CheckOperation,
    ComparisonOperationEnum,
    OutputStatements,
    FixDetails,
)

class YamlChecksLoader(object):
    def __init__(
            self,
            checks_directory: Path
    ):
        """
        Load YAML check contents.

        Args:
            checks_directory: Directory containing YAML files
        """
        self.checks_directory = checks_directory
        # "llm_generator/data/debugging_BKP/sec3_checks_with_python_logic/step4_consolidate_repaired_checks/output"

    @property
    def resource_provider_mapping(
            self
    ) -> Dict[str, str]:
        return {
            "GithubResource": "github",
            "EC2Resource": "aws",
            "S3Resource": "aws",
            "IAMResource": "aws",
            "CloudTrailResource": "aws",
            "CloudWatchResource": "aws",
            "UserResource": "google",
            "GroupResource": "google",
        }

    def get_check_object(
            self,
            check_name: str
    ) -> Check:
        """
        Load check configuration from YAML and convert to Check object.

        Args:
            check_name: Name of the check to load

        Returns:
            Check: Configured Check object ready for evaluation
        """
        # Load YAML content
        yaml_content = self.yaml_safe_load(check_name)

        # Extract check data from YAML structure
        check_data = yaml_content.get('check', {})
        resource_name = check_data['resource']['name']
        provider = self.resource_provider_mapping[resource_name]
        resource_type = f"con_mon.mappings.{provider}.{resource_name}"

        # Build the Check object
        print(f'Building check object for {check_name}')
        check_obj = Check(
            # id=check_data.get('unique_id', check_name),
            # name=check_data.get('name', check_name),
            id=check_name,
            name=check_name,
            description=check_data.get('description', ''),

            # Build nested JSONB structures
            metadata=CheckMetadata(
                tags=check_data.get('resource', {}).get('tags', []),
                category=check_data.get('category', 'security'),
                severity=check_data.get('severity', 'medium'),
                operation=CheckOperation(
                    name=ComparisonOperationEnum.CUSTOM,
                    logic=check_data.get('resource', {}).get('logic', '')
                ),
                field_path=check_data.get('resource', {}).get('field_path', ''),
                resource_type=resource_type,
                expected_value=check_data.get('resource', {}).get('expected_value')
            ),

            output_statements=OutputStatements(
                failure=check_data.get('resource', {}).get('output_statements', {}).get('failure', ''),
                partial=check_data.get('resource', {}).get('output_statements', {}).get('partial', ''),
                success=check_data.get('resource', {}).get('output_statements', {}).get('success', '')
            ),

            fix_details=FixDetails(
                description=check_data.get('resource', {}).get('fix_details', {}).get('description', ''),
                instructions=check_data.get('resource', {}).get('fix_details', {}).get('instructions', []),
                estimated_time=check_data.get('resource', {}).get('fix_details', {}).get('estimated_time', 'unknown'),
                automation_available=check_data.get('resource', {}).get('fix_details', {}).get('automation_available', False)
            ),

            # Default values for required fields
            created_by='system',
            category=check_data.get('category', 'security'),
            updated_by='system',
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_deleted=False
        )

        return check_obj


    def yaml_safe_load(
            self,
            check_name: str
    ) -> Dict[str, Any]:
        """
        Load YAML content for the given check name.
        This function should be implemented to load from your YAML source
        (file system, database, etc.)

        Args:
            check_name: Name of the check to load

        Returns:
            Dict containing the parsed YAML content
        """
        # Placeholder implementation - replace with your actual YAML loading logic
        # This could load from files, database, API, etc.

        # Example implementation for file loading:
        with open(f"{self.checks_directory}/{check_name}.yaml", 'r') as f:
            return yaml.safe_load(f)

    @property
    def load_all_checks(
            self,
    ) -> List[Check]:
        """
        Load all YAML check files from a directory and convert to Check objects.

        Args:
            checks_directory: Directory containing YAML files

        Returns:
            Dict mapping check names to Check objects

        Raises:
            FileNotFoundError: If directory doesn't exist
            yaml.YAMLError: If any YAML parsing fails
            ValueError: If check conversion fails
        """
        if not os.path.exists(self.checks_directory):
            raise FileNotFoundError(f"Checks directory not found: {self.checks_directory}")

        checks: List[Check] = []

        # Find all YAML files in directory
        yaml_patterns = [
            os.path.join(self.checks_directory, "*.yaml"),
            os.path.join(self.checks_directory, "*.yml")
        ]

        yaml_files = []
        for pattern in yaml_patterns:
            yaml_files.extend(glob.glob(pattern))

        print(f"Found {len(yaml_files)} YAML files in {self.checks_directory}")

        for file_path in yaml_files:
            try:
                # Extract check name from filename
                check_name = Path(file_path).stem

                print(f"Loading check: {check_name}")

                # Load and convert to Check object
                check_obj = self.get_check_object(check_name)
                # checks[check_name] = check_obj
                checks.append(check_obj)

            except Exception as e:
                print(f"Error loading check from {file_path}: {e}")
                # Continue loading other files, don't fail completely
                continue

        print(f"Successfully loaded {len(checks)} checks")
        return checks
