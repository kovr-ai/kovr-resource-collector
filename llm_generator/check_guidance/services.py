"""
Check Guidance Service - Section 2 System Compatibility Implementation

This module implements system compatibility enrichment workflow:
1. Expand to Resource Types and Field Paths
2. Coverage on System Compatibility

Provides check_guidance_service instance for external usage.
"""

import json
import logging
from typing import Dict, Any, List
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Local imports - prompts
from .prompts import (
    get_system_enrichment_prompt,
    get_resource_selection_prompt,
    generate_system_enriched_id,
)
from .models import (
    SystemEnrichedCheck,
    ResourceSchema,
    SystemCompatibilityCoverage
)

# System imports
from con_mon.utils.llm.client import get_llm_client
from con_mon.resources.dynamic_models import get_dynamic_models

logger = logging.getLogger(__name__)


class CheckGuidanceService:
    """
    Core service for system compatibility enrichment implementing Section 2 workflow.

    Methods align with the 2-step process:
    - enrich_checks_with_system_resources(): Step 1 - Expand to Resource Types and Field Paths
    - generate_system_compatibility_coverage(): Step 2 - Coverage on System Compatibility
    """

    def __init__(self):
        self.llm_client = get_llm_client()
        self._resource_schemas_cache = None

    def enrich_checks_with_system_resources(
            self,
            enriched_checks: List,  # List of Check objects from Section 1
            thread_count: int = 1,
    ) -> List[SystemEnrichedCheck]:
        """
        Step 1: Expand checks to include resource types and field paths.

        Args:
            enriched_checks: List of enriched Check objects from Section 1
            thread_count: Number of threads to use for parallel processing (default: 1)

        Returns:
            List of SystemEnrichedCheck objects with system compatibility info
        """
        logger.info(f"Starting Step 1: Enriching {len(enriched_checks)} checks with system resources")

        # Load available resource schemas
        resource_schemas = self._load_resource_schemas()
        logger.info(f"Loaded {len(resource_schemas)} resource schemas")

        # Process checks in parallel using threading
        if thread_count == 1:
            # Single-threaded processing (preserve original logging behavior)
            system_enriched_checks = []
            for i, check in enumerate(enriched_checks):
                logger.info(f"Enriching check {i + 1}/{len(enriched_checks)}: {check.unique_id}")
                system_enriched_check = self._process_single_check(check, resource_schemas)
                system_enriched_checks.append(system_enriched_check)
        else:
            # Multi-threaded processing
            logger.info(f"Using {thread_count} threads for parallel processing...")
            system_enriched_checks = []
            
            with ThreadPoolExecutor(max_workers=thread_count) as executor:
                # Submit all tasks
                future_to_check = {
                    executor.submit(self._process_single_check, check, resource_schemas): check 
                    for check in enriched_checks
                }
                
                # Collect results as they complete
                completed = 0
                for future in as_completed(future_to_check):
                    completed += 1
                    check = future_to_check[future]
                    
                    try:
                        result = future.result()
                        system_enriched_checks.append(result)
                        logger.info(f"✅ Completed {completed}/{len(enriched_checks)}: {check.unique_id}")
                    except Exception as e:
                        logger.error(f"❌ Failed to process check {check.unique_id}: {e}")
                        # Create fallback check
                        fallback_check = self._create_fallback_enriched_check(check)
                        system_enriched_checks.append(fallback_check)

        logger.info(f"Successfully enriched {len(system_enriched_checks)} checks with system resources")
        return system_enriched_checks

    def _process_single_check(self, check, resource_schemas: List[ResourceSchema]) -> SystemEnrichedCheck:
        """Process a single check with system enrichment (thread-safe)."""
        try:
            # Step 1: Generate system-enriched check using LLM
            check_data = self._check_to_dict(check)
            resource_schemas_data = [self._resource_schema_to_dict(rs) for rs in resource_schemas]
            
            enrichment_prompt = get_system_enrichment_prompt(check_data, resource_schemas_data)
            enrichment_response = self.llm_client.generate_text(enrichment_prompt)

            # Parse system-enriched check from LLM
            enriched_check_data = self._parse_json_response(enrichment_response)

            # Validate field paths against available schemas
            validated_field_paths = self._validate_field_paths(
                enriched_check_data.get('field_paths_used', []),
                enriched_check_data.get('resource_type', ''),
                resource_schemas
            )

            # Create SystemEnrichedCheck object
            system_enriched_check = SystemEnrichedCheck(
                unique_id=enriched_check_data.get('unique_id', check.unique_id),
                name=enriched_check_data.get('name', check.name),
                literature=enriched_check_data.get('literature', check.literature),
                controls=check.controls or [],
                frameworks=check.frameworks or [],
                benchmark_mapping=check.benchmark_mapping or [],
                mapping_confidence=check.mapping_confidence or 0.0,
                category=check.category or '',
                severity=check.severity or 'medium',
                tags=check.tags or [],
                extracted_at=check.extracted_at,
                mapped_at=check.mapped_at,
                resource_type=enriched_check_data.get('resource_type', ''),
                field_paths_used=validated_field_paths,
                targeted_guidance=enriched_check_data.get('targeted_guidance', ''),
                system_enriched_at=datetime.now()
            )

            return system_enriched_check
            
        except Exception as e:
            logger.error(f"Failed to enrich check {check.unique_id}: {e}")
            return self._create_fallback_enriched_check(check)

    def _create_fallback_enriched_check(self, check) -> SystemEnrichedCheck:
        """Create a fallback SystemEnrichedCheck when processing fails."""
        return SystemEnrichedCheck(
            unique_id=check.unique_id,
            name=check.name,
            literature=check.literature,
            controls=check.controls or [],
            frameworks=check.frameworks or [],
            benchmark_mapping=check.benchmark_mapping or [],
            mapping_confidence=check.mapping_confidence or 0.0,
            category=check.category or '',
            severity=check.severity or 'medium',
            tags=check.tags or [],
            extracted_at=check.extracted_at,
            mapped_at=check.mapped_at,
            resource_type='No Compatible Resource',
            field_paths_used=[],
            targeted_guidance='System compatibility could not be determined.',
            system_enriched_at=datetime.now()
        )

    def generate_system_compatibility_coverage(
            self, 
            system_enriched_checks: List[SystemEnrichedCheck]
    ) -> SystemCompatibilityCoverage:
        """
        Step 2: Generate coverage metrics for system compatibility.

        Args:
            system_enriched_checks: List of SystemEnrichedCheck objects from Step 1

        Returns:
            SystemCompatibilityCoverage object containing coverage statistics
        """
        total_checks = len(system_enriched_checks)
        
        checks_with_resource_types = sum(
            1 for check in system_enriched_checks 
            if check.resource_type and check.resource_type != 'No Compatible Resource'
        )
        
        checks_with_field_paths = sum(
            1 for check in system_enriched_checks 
            if check.field_paths_used
        )
        
        checks_with_targeted_guidance = sum(
            1 for check in system_enriched_checks 
            if check.targeted_guidance and len(check.targeted_guidance.strip()) > 50
        )

        # Provider breakdown
        github_checks = sum(1 for check in system_enriched_checks if 'GitHub' in (check.resource_type or ''))
        aws_checks = sum(1 for check in system_enriched_checks if 'AWS' in (check.resource_type or ''))
        google_checks = sum(1 for check in system_enriched_checks if 'Google' in (check.resource_type or ''))
        
        # Quality metrics
        total_field_paths = sum(len(check.field_paths_used or []) for check in system_enriched_checks)
        avg_field_paths = (total_field_paths / total_checks) if total_checks > 0 else 0
        
        total_guidance_length = sum(len(check.targeted_guidance or '') for check in system_enriched_checks)
        avg_guidance_length = (total_guidance_length / total_checks) if total_checks > 0 else 0
        
        checks_with_multiple_resources = sum(
            1 for check in system_enriched_checks 
            if (check.field_paths_used and len(check.field_paths_used) > 1)
        )

        return SystemCompatibilityCoverage(
            total_checks=total_checks,
            checks_with_resource_types=checks_with_resource_types,
            checks_with_field_paths=checks_with_field_paths,
            checks_with_targeted_guidance=checks_with_targeted_guidance,
            coverage_percentages={
                'resource_types': (checks_with_resource_types / total_checks * 100) if total_checks > 0 else 0,
                'field_paths': (checks_with_field_paths / total_checks * 100) if total_checks > 0 else 0,
                'targeted_guidance': (checks_with_targeted_guidance / total_checks * 100) if total_checks > 0 else 0
            },
            provider_coverage={
                'github_checks': github_checks,
                'aws_checks': aws_checks, 
                'google_checks': google_checks,
                'multi_provider_checks': checks_with_multiple_resources
            },
            quality_metrics={
                'avg_field_paths_per_check': avg_field_paths,
                'avg_guidance_length': avg_guidance_length,
                'checks_with_multiple_resources': checks_with_multiple_resources
            }
        )

    # Helper methods
    def _load_resource_schemas(self) -> List[ResourceSchema]:
        """Load available resource schemas for system compatibility."""
        if self._resource_schemas_cache is None:
            # Use enhanced resource schemas with proper field paths for security checks
            self._resource_schemas_cache = self._get_enhanced_resource_schemas()
            logger.info(f"Loaded {len(self._resource_schemas_cache)} enhanced resource schemas")
                
        return self._resource_schemas_cache

    def _extract_field_paths_from_model(self, model_class) -> List[str]:
        """Extract field paths from resource model."""
        try:
            # Use the field_paths method from the Resource base class
            if hasattr(model_class, 'field_paths'):
                return model_class.field_paths(max_depth=3)
            else:
                # Fallback to basic field introspection
                field_paths = []
                if hasattr(model_class, 'model_fields'):
                    for field_name in model_class.model_fields.keys():
                        field_paths.append(field_name)
                elif hasattr(model_class, '__fields__'):
                    for field_name in model_class.__fields__.keys():
                        field_paths.append(field_name)
                return field_paths
        except Exception as e:
            logger.warning(f"Failed to extract field paths from {model_class.__name__}: {e}")
            return []

    def _convert_model_name_to_resource_type(self, model_name: str) -> str:
        """Convert model name to resource type format."""
        if model_name.startswith('Github'):
            return f"GitHub::{model_name.replace('Github', '')}"
        elif model_name.startswith('AWS'):
            # Handle AWS models like AWSEC2Resource -> AWS::EC2::Instance
            service_part = model_name.replace('AWS', '').replace('Resource', '')
            if service_part == 'EC2':
                return "AWS::EC2::Instance"
            elif service_part == 'IAM':
                return "AWS::IAM::Role"
            elif service_part == 'S3':
                return "AWS::S3::Bucket"
            elif service_part == 'CloudTrail':
                return "AWS::CloudTrail::Trail"
            elif service_part == 'CloudWatch':
                return "AWS::CloudWatch::Alarm"
            else:
                return f"AWS::{service_part}"
        else:
            return model_name.replace('Resource', '')
    
    def _extract_provider_from_model_name(self, model_name: str) -> str:
        """Extract provider name from model name."""
        if model_name.startswith('Github'):
            return 'github'
        elif model_name.startswith('AWS'):
            return 'aws'
        elif model_name.startswith('Google'):
            return 'google'
        else:
            return 'unknown'

    def _extract_provider_from_resource_type(self, resource_type: str) -> str:
        """Extract provider name from resource type."""
        if '::' in resource_type:
            return resource_type.split('::')[0].lower()
        elif resource_type.startswith(('GitHub', 'github')):
            return 'github'
        elif resource_type.startswith(('AWS', 'aws')):
            return 'aws'
        elif resource_type.startswith(('Google', 'google', 'GCP')):
            return 'google'
        else:
            return 'unknown'

    def _get_enhanced_resource_schemas(self) -> List[ResourceSchema]:
        """Get enhanced resource schemas with comprehensive field paths for security checks."""
        return self._get_fallback_resource_schemas()

    def _get_fallback_resource_schemas(self) -> List[ResourceSchema]:
        """Provide fallback resource schemas if loading fails."""
        return [
            ResourceSchema(
                resource_type="GitHub::Repo",
                display_name="GitHub Repository",
                field_paths=[
                    "repo.basic_info.name",
                    "repo.basic_info.description",
                    "repo.basic_info.visibility",
                    "repo.basic_info.default_branch",
                    "repo.basic_info.branches[].name", 
                    "repo.basic_info.branches[].protected",
                    "repo.security.branch_protection.enforce_admins",
                    "repo.security.branch_protection.required_reviews",
                    "repo.security.branch_protection.dismiss_stale_reviews",
                    "repo.security.branch_protection.require_code_owner_reviews",
                    "repo.security.vulnerability_alerts_enabled",
                    "repo.security.secret_scanning_enabled",
                    "repo.security.dependabot_alerts_enabled",
                    "repo.security.security_policy.url",
                    "repo.collaborators[].login",
                    "repo.collaborators[].permissions.admin",
                    "repo.collaborators[].permissions.push",
                    "repo.collaborators[].permissions.pull",
                    "repo.webhooks[].url",
                    "repo.webhooks[].events[]",
                    "repo.webhooks[].active"
                ],
                provider="github",
                description="GitHub repository with comprehensive security and access control settings"
            ),
            ResourceSchema(
                resource_type="AWS::EC2::Instance",
                display_name="AWS EC2 Instance", 
                field_paths=[
                    "instance.instance_id",
                    "instance.state",
                    "instance.security_groups[].group_id",
                    "instance.vpc_id",
                    "instance.tags[]"
                ],
                provider="aws",
                description="AWS EC2 compute instance"
            ),
            ResourceSchema(
                resource_type="Google::Compute::Instance",
                display_name="Google Compute Instance",
                field_paths=[
                    "instance.name",
                    "instance.status", 
                    "instance.machine_type",
                    "instance.network_interfaces[].access_configs",
                    "instance.service_accounts[].scopes"
                ],
                provider="google",
                description="Google Cloud compute instance"
            )
        ]

    def _validate_field_paths(self, field_paths: List[str], resource_type: str, resource_schemas: List[ResourceSchema]) -> List[str]:
        """Validate that field paths actually exist in the resource schema."""
        if not field_paths or not resource_type:
            return []
            
        # Find matching resource schema
        matching_schema = next((rs for rs in resource_schemas if rs.resource_type == resource_type), None)
        if not matching_schema:
            return []
            
        # Filter field paths to only include valid ones
        valid_paths = [fp for fp in field_paths if fp in matching_schema.field_paths]
        
        if len(valid_paths) < len(field_paths):
            invalid_paths = set(field_paths) - set(valid_paths)
            logger.warning(f"Filtered out invalid field paths for {resource_type}: {invalid_paths}")
            
        return valid_paths

    def _check_to_dict(self, check) -> Dict[str, Any]:
        """Convert Check object to dictionary for LLM processing."""
        return {
            'unique_id': check.unique_id,
            'name': check.name,
            'literature': check.literature,
            'controls': check.controls or [],
            'frameworks': check.frameworks or [],
            'benchmark_mapping': check.benchmark_mapping or [],
            'mapping_confidence': check.mapping_confidence or 0.0,
            'category': check.category or '',
            'severity': check.severity or 'medium',
            'tags': check.tags or [],
            'extracted_at': check.extracted_at.isoformat() if hasattr(check.extracted_at, 'isoformat') else str(check.extracted_at),
            'mapped_at': check.mapped_at.isoformat() if hasattr(check.mapped_at, 'isoformat') else str(check.mapped_at)
        }

    def _resource_schema_to_dict(self, resource_schema: ResourceSchema) -> Dict[str, Any]:
        """Convert ResourceSchema object to dictionary for LLM processing."""
        return {
            'resource_type': resource_schema.resource_type,
            'display_name': resource_schema.display_name,
            'field_paths': resource_schema.field_paths,
            'provider': resource_schema.provider,
            'description': resource_schema.description
        }

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response from LLM with enhanced error handling."""
        
        def clean_json_string(json_str: str) -> str:
            """Clean JSON string by handling control characters."""
            import re
            
            # Replace common control characters with their escaped equivalents
            # but be careful to only replace them inside string values, not JSON structure
            
            # First, let's handle the most common issue: unescaped newlines in string values
            # We'll use a more sophisticated approach that preserves JSON structure
            
            # Replace unescaped control characters in string values
            # This regex finds strings and replaces control characters within them
            def replace_control_chars(match):
                string_content = match.group(1)
                # Replace control characters with their escaped equivalents
                string_content = string_content.replace('\n', '\\n')
                string_content = string_content.replace('\r', '\\r')
                string_content = string_content.replace('\t', '\\t')
                string_content = string_content.replace('\b', '\\b')
                string_content = string_content.replace('\f', '\\f')
                # Handle other control characters (ASCII 0-31 except those already handled)
                for i in range(32):
                    char = chr(i)
                    if char not in ['\n', '\r', '\t', '\b', '\f']:
                        string_content = string_content.replace(char, f'\\u{i:04x}')
                return f'"{string_content}"'
            
            # Apply the replacement to all string values
            # This regex matches quoted strings, accounting for escaped quotes
            json_str = re.sub(r'"((?:[^"\\]|\\.)*)(?<!\\)"', replace_control_chars, json_str)
            
            return json_str
        
        try:
            # First attempt: parse as-is
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}")
            logger.info(f"LLM Response (first 500 chars): {response[:500]}")

            # Try to extract JSON from markdown code blocks
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                logger.info("Found JSON in markdown code block, attempting to parse...")
                json_content = json_match.group(1).strip()
                
                try:
                    # Try parsing the extracted JSON as-is first
                    return json.loads(json_content)
                except json.JSONDecodeError as e2:
                    logger.info(f"JSON parsing failed, attempting to clean control characters: {e2}")
                    # Clean the JSON string and try again
                    try:
                        cleaned_json = clean_json_string(json_content)
                        logger.debug(f"Cleaned JSON (first 500 chars): {cleaned_json[:500]}")
                        return json.loads(cleaned_json)
                    except json.JSONDecodeError as e3:
                        logger.error(f"Failed to parse even after cleaning: {e3}")
                        logger.debug(f"Cleaned JSON content: {cleaned_json}")
                        # As a last resort, try to create a basic fallback structure
                        return self._create_fallback_response()

            # If no markdown block found, try cleaning the original response
            try:
                cleaned_response = clean_json_string(response.strip())
                return json.loads(cleaned_response)
            except json.JSONDecodeError:
                logger.error("All JSON parsing attempts failed, using fallback response")
                return self._create_fallback_response()

    def _create_fallback_response(self) -> Dict[str, Any]:
        """Create a fallback response when JSON parsing fails."""
        return {
            "unique_id": "parsing_failed",
            "name": "JSON Parsing Failed",
            "literature": "Failed to parse LLM response due to JSON formatting issues.",
            "controls": [],
            "frameworks": [],
            "benchmark_mapping": [],
            "mapping_confidence": 0.0,
            "category": "Unknown",
            "severity": "unknown",
            "tags": ["parsing-error"],
            "extracted_at": datetime.now().isoformat(),
            "mapped_at": datetime.now().isoformat(),
            "resource_type": "No Compatible Resource",
            "field_paths_used": [],
            "targeted_guidance": "Unable to generate guidance due to parsing errors.",
            "system_enriched_at": datetime.now().isoformat()
        }


# Global service instance for external usage
check_guidance_service = CheckGuidanceService()

# Export the key methods
enrich_checks_with_system_resources = check_guidance_service.enrich_checks_with_system_resources
generate_system_compatibility_coverage = check_guidance_service.generate_system_compatibility_coverage
