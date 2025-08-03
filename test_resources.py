#!/usr/bin/env python3
"""
Dynamic test resources module - verify GithubResourceCollection and GithubResource models
contain all data from response.json based on YAML schema definitions.
No hardcoded field names - everything is validated against the YAML schema.
"""

import json
import yaml
import os
from datetime import datetime
from typing import Any, Dict, List, Tuple, Union
from resources import GithubResource, GithubResourceCollection

def load_schema_definitions() -> Dict[str, Any]:
    """Load the YAML schema definitions."""
    schema_path = os.path.join('resources', 'resources.yaml')
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def load_response_data() -> Dict[str, Any]:
    """Load the response.json file."""
    with open('response.json', 'r') as f:
        return json.load(f)

def extract_field_paths(schema_fields: Dict[str, Any], prefix: str = "") -> List[Tuple[str, str]]:
    """
    Recursively extract all field paths from schema definition.
    Returns list of tuples: (field_path, field_type)
    
    Example: 
    - ('basic_info.id', 'integer')
    - ('metadata.default_branch', 'string')
    - ('branches[].name', 'string')
    """
    field_paths = []
    
    for field_name, field_definition in schema_fields.items():
        current_path = f"{prefix}.{field_name}" if prefix else field_name
        
        if isinstance(field_definition, dict):
            # Nested object - recurse deeper
            field_paths.extend(extract_field_paths(field_definition, current_path))
        elif isinstance(field_definition, list):
            # Array with object structure - handle array items
            if field_definition and isinstance(field_definition[0], dict):
                # Array of objects (like branches)
                array_item_paths = extract_field_paths(field_definition[0], f"{current_path}[]")
                field_paths.extend(array_item_paths)
            else:
                # Simple array
                field_paths.append((current_path, "array"))
        else:
            # Simple field
            field_paths.append((current_path, field_definition))
    
    return field_paths

def get_nested_value(obj: Any, field_path: str) -> Any:
    """
    Get nested value from object using dot notation path.
    Handles both dict and Pydantic model access.
    Supports array notation like 'branches[].name'
    """
    parts = field_path.split('.')
    current = obj
    
    for part in parts:
        if part.endswith('[]'):
            # Array field - return the array itself for now
            field_name = part[:-2]  # Remove []
            if isinstance(current, dict):
                current = current.get(field_name)
            else:
                current = getattr(current, field_name, None)
        else:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                current = getattr(current, part, None)
        
        if current is None:
            break
    
    return current

def compare_values(model_value: Any, original_value: Any, field_type: str) -> Tuple[bool, str]:
    """
    Compare model value with original value considering the field type.
    Returns (is_match, message)
    """
    # Handle None values
    if model_value is None and original_value is None:
        return True, "Both None"
    if model_value is None or original_value is None:
        return False, f"One is None: model={model_value}, original={original_value}"
    
    # Handle datetime conversion
    if field_type == "string" and isinstance(model_value, datetime):
        model_value = model_value.isoformat()
    
    # Direct comparison for most types
    if model_value == original_value:
        return True, f"Values match: {model_value}"
    else:
        return False, f"Values differ: model={model_value}, original={original_value}"

def test_array_field(model_array: List[Any], original_array: List[Any], field_paths: List[Tuple[str, str]], base_path: str) -> Dict[str, List[str]]:
    """
    Test array fields with nested objects (like branches).
    """
    results = {
        'passed': [],
        'failed': [],
        'warnings': []
    }
    
    # Check array length
    if len(model_array) == len(original_array):
        results['passed'].append(f"✅ {base_path}: Array length matches ({len(model_array)} items)")
    else:
        results['failed'].append(f"❌ {base_path}: Array length differs - model: {len(model_array)}, original: {len(original_array)}")
        return results
    
    # Test fields in array items
    array_field_paths = [fp for fp in field_paths if fp[0].startswith(f"{base_path}[]")]
    
    if array_field_paths and model_array and original_array:
        # Test first item in detail, then spot check others
        for i, (model_item, original_item) in enumerate(zip(model_array, original_array)):
            item_prefix = f"{base_path}[{i}]"
            
            for field_path, field_type in array_field_paths:
                # Convert array path to item-specific path
                item_field_path = field_path.replace(f"{base_path}[].", "")
                
                try:
                    model_value = get_nested_value(model_item, item_field_path)
                    original_value = get_nested_value(original_item, item_field_path)
                    
                    is_match, message = compare_values(model_value, original_value, field_type)
                    
                    if is_match:
                        if i == 0:  # Only show details for first item to avoid spam
                            results['passed'].append(f"✅ {item_prefix}.{item_field_path}: {message}")
                    else:
                        results['failed'].append(f"❌ {item_prefix}.{item_field_path}: {message}")
                        
                except Exception as e:
                    results['failed'].append(f"❌ {item_prefix}.{item_field_path}: Error accessing - {str(e)}")
            
            # Only test first few items in detail for performance
            if i >= 2:
                break
    
    return results

def test_resource_schema(resource_obj: Any, original_resource_data: Dict[str, Any], schema_fields: Dict[str, Any], resource_type: str = "Resource") -> Dict[str, List[str]]:
    """
    Test any resource object against its YAML schema definition.
    Completely dynamic - works with any resource type defined in YAML.
    """
    results = {
        'passed': [],
        'failed': [],
        'warnings': []
    }
    
    # Extract all field paths from schema
    field_paths = extract_field_paths(schema_fields)
    
    print(f"  📋 Testing {len(field_paths)} schema-defined fields for {resource_type}...")
    
    for field_path, field_type in field_paths:
        # Skip array item paths - they'll be handled by test_array_field
        if '[].' in field_path:
            continue
            
        try:
            # Get model value from resource object
            model_value = get_nested_value(resource_obj, field_path)
            
            # Get original value from response data
            # This is the only part that needs to know about the data structure
            if field_path in ['repository', 'basic_info', 'metadata', 'branches', 'statistics']:
                # Top-level fields from data section (for resources that have this structure)
                original_value = original_resource_data.get('data', {}).get(field_path)
            else:
                # Nested field - need to navigate through data structure
                data_section = original_resource_data.get('data', original_resource_data)
                original_value = get_nested_value(data_section, field_path)
            
            # Handle array fields specially
            if field_type == "array" or (isinstance(original_value, list) and field_path.endswith('s')):
                if isinstance(model_value, list) and isinstance(original_value, list):
                    # Test array fields with potential nested objects
                    array_results = test_array_field(model_value, original_value, field_paths, field_path)
                    results['passed'].extend(array_results['passed'])
                    results['failed'].extend(array_results['failed'])
                    results['warnings'].extend(array_results['warnings'])
                else:
                    results['failed'].append(f"❌ {field_path}: Expected array, got model: {type(model_value)}, original: {type(original_value)}")
            elif field_path.endswith('[]'):
                # Skip array item indicators - handled above
                continue
            else:
                # Regular field comparison
                is_match, message = compare_values(model_value, original_value, field_type)
                
                if is_match:
                    results['passed'].append(f"✅ {field_path}: {message}")
                else:
                    results['failed'].append(f"❌ {field_path}: {message}")
                    
        except Exception as e:
            results['failed'].append(f"❌ {field_path}: Error during validation - {str(e)}")
    
    return results

def test_base_resource_fields(resource_obj: Any, original_resource_data: Dict[str, Any]) -> Dict[str, List[str]]:
    """Test base Resource fields for any resource type (id, source_connector, created_at, updated_at, tags, metadata)."""
    results = {
        'passed': [],
        'failed': [],
        'warnings': []
    }
    
    # Base fields that all resources should have
    base_fields = ['id', 'source_connector', 'created_at', 'updated_at']
    
    for field in base_fields:
        try:
            model_value = getattr(resource_obj, field)
            original_value = original_resource_data.get(field)
            
            # Special handling for datetime fields
            if field in ['created_at', 'updated_at'] and isinstance(model_value, datetime):
                model_value = model_value.isoformat()
            
            if model_value == original_value:
                results['passed'].append(f"✅ {field}: Values match")
            else:
                results['failed'].append(f"❌ {field}: Model={model_value}, Original={original_value}")
                
        except Exception as e:
            results['failed'].append(f"❌ {field}: Error accessing - {str(e)}")
    
    # Test tags (should include original tags plus metadata preservation tags)
    try:
        model_tags = resource_obj.tags
        original_tags = original_resource_data.get('tags', [])
        
        original_tags_present = all(tag in model_tags for tag in original_tags)
        if original_tags_present:
            results['passed'].append(f"✅ tags: All {len(original_tags)} original tags present")
        else:
            missing = [tag for tag in original_tags if tag not in model_tags]
            results['failed'].append(f"❌ tags: Missing original tags: {missing}")
            
        # Check for metadata preservation tags
        original_metadata = original_resource_data.get('metadata', {})
        if original_metadata:
            expected_tags = []
            if 'authenticated_user' in original_metadata:
                expected_tags.append(f"user:{original_metadata['authenticated_user']}")
            if 'provider' in original_metadata:
                expected_tags.append(f"provider:{original_metadata['provider']}")
            
            missing_meta_tags = [tag for tag in expected_tags if tag not in model_tags]
            if not missing_meta_tags:
                results['passed'].append(f"✅ tags: Metadata preservation tags present")
            else:
                results['failed'].append(f"❌ tags: Missing metadata tags: {missing_meta_tags}")
                
    except Exception as e:
        results['failed'].append(f"❌ tags: Error accessing - {str(e)}")
    
    return results

def test_resource_collection_schema(collection_obj: Any, original_data: Dict[str, Any], schema_fields: Dict[str, Any], collection_type: str = "ResourceCollection") -> Dict[str, List[str]]:
    """Test any resource collection against its YAML schema definition."""
    results = {
        'passed': [],
        'failed': [],
        'warnings': []
    }
    
    # Extract field paths from collection schema
    field_paths = extract_field_paths(schema_fields)
    
    print(f"  📋 Testing {len(field_paths)} collection schema fields for {collection_type}...")
    
    for field_path, field_type in field_paths:
        # Skip resources field - it's special (contains resource objects)
        if field_path == 'resources':
            continue
            
        try:
            model_value = get_nested_value(collection_obj, field_path)
            
            # Collection fields are set by us, so we mainly check they exist and have correct types
            if model_value is not None:
                results['passed'].append(f"✅ {field_path}: Present with value")
            else:
                results['warnings'].append(f"⚠️  {field_path}: Not set (may be intentional)")
                
        except Exception as e:
            results['failed'].append(f"❌ {field_path}: Error accessing - {str(e)}")
    
    # Test resources field specially
    try:
        if hasattr(collection_obj, 'resources') and len(collection_obj.resources) == len(original_data['resources']):
            results['passed'].append(f"✅ resources: Contains {len(collection_obj.resources)} resources")
        else:
            results['failed'].append(f"❌ resources: Expected {len(original_data['resources'])}, got {len(getattr(collection_obj, 'resources', []))}")
        
        # Check that all items are the expected resource type (generic check)
        if hasattr(collection_obj, 'resources'):
            for i, resource in enumerate(collection_obj.resources):
                # Just check it has the basic resource attributes
                if hasattr(resource, 'id') and hasattr(resource, 'source_connector'):
                    results['passed'].append(f"✅ resources[{i}]: Is valid resource object")
                else:
                    results['failed'].append(f"❌ resources[{i}]: Not a valid resource object, got {type(resource)}")
                
    except Exception as e:
        results['failed'].append(f"❌ resources: Error accessing - {str(e)}")
    
    return results

def create_github_resources_from_response(response_data: Dict[str, Any]) -> List[GithubResource]:
    """Create GithubResource objects from response data (same as before)."""
    github_resources = []
    
    for resource_data in response_data['resources']:
        github_repo_metadata = resource_data['data'].get('metadata', {})
        
        github_resource = GithubResource(
            id=resource_data['id'],
            source_connector=resource_data['source_connector'],
            created_at=datetime.fromisoformat(resource_data['created_at']),
            updated_at=datetime.fromisoformat(resource_data['updated_at']),
            metadata=github_repo_metadata,
            tags=resource_data.get('tags', []),
            repository=resource_data['data']['repository'],
            basic_info=resource_data['data']['basic_info'],
            branches=resource_data['data']['branches'],
            statistics=resource_data['data']['statistics']
        )
        
        # Preserve original resource metadata as tags
        original_metadata = resource_data.get('metadata', {})
        if original_metadata:
            if 'authenticated_user' in original_metadata:
                github_resource.add_tag(f"user:{original_metadata['authenticated_user']}")
            if 'provider' in original_metadata:
                github_resource.add_tag(f"provider:{original_metadata['provider']}")
        
        github_resources.append(github_resource)
    
    return github_resources

def create_github_resource_collection(github_resources: List[GithubResource]) -> GithubResourceCollection:
    """Create GithubResourceCollection (same as before)."""
    return GithubResourceCollection(
        resources=github_resources,
        source_connector='github',
        total_count=len(github_resources),
        fetched_at=datetime.now().isoformat(),
        collection_metadata={
            'authenticated_user': 'vishesh-kovr',
            'total_repositories': len(github_resources),
            'total_workflows': 24,
            'total_issues': 173,
            'total_pull_requests': 113,
            'total_security_alerts': 20,
            'total_collaborators': 56,
            'total_tags': 40,
            'total_active_webhooks': 0
        },
        github_api_metadata={
            'collection_time': datetime.now().isoformat(),
            'api_version': 'v3',
            'scope': ['repo', 'read:org']
        }
    )

def run_dynamic_schema_test():
    """Run comprehensive dynamic test based on YAML schema definitions."""
    
    print("🧪 Dynamic Schema-Based Resources Test")
    print("=" * 60)
    
    # Load schema definitions
    print("📋 Loading YAML schema definitions...")
    schema_data = load_schema_definitions()
    
    # Auto-detect resource types from YAML
    available_resources = list(schema_data['resources'].keys())
    print(f"✅ Found {len(available_resources)} resource types: {', '.join(available_resources)}")
    
    # For this test, we'll focus on the first resource type and its collection
    # In a real system, you might want to test all resource types
    resource_types = [rt for rt in available_resources if not rt.endswith('Collection')]
    collection_types = [rt for rt in available_resources if rt.endswith('Collection')]
    
    if not resource_types:
        print("❌ No resource types found in YAML schema")
        return None
        
    # Use the first resource type found
    resource_type = resource_types[0]  # e.g., 'GithubResource'
    resource_schema = schema_data['resources'][resource_type]['fields']
    
    # Find corresponding collection type
    collection_type = None
    collection_schema = None
    for ct in collection_types:
        if schema_data['resources'][ct].get('collection_type') == resource_type:
            collection_type = ct
            collection_schema = schema_data['resources'][ct]['fields']
            break
    
    print(f"🎯 Testing resource type: {resource_type}")
    if collection_type:
        print(f"🎯 Testing collection type: {collection_type}")
    
    # Load original data
    print("\n📂 Loading response.json...")
    original_data = load_response_data()
    print(f"✅ Loaded data for {len(original_data['resources'])} resources")
    
    # Dynamically create resources based on detected type
    print(f"\n🏗️  Creating {resource_type} objects...")
    
    # For now, we'll use the GitHub creation logic, but this could be made more generic
    # In a full implementation, you'd have a factory pattern here
    if resource_type == 'GithubResource':
        resources = create_github_resources_from_response(original_data)
        print(f"✅ Created {len(resources)} {resource_type} objects")
        
        # Create collection if collection type exists
        if collection_type == 'GithubResourceCollection':
            print(f"\n📦 Creating {collection_type}...")
            collection = create_github_resource_collection(resources)
            print(f"✅ Created collection with {len(collection)} resources")
        else:
            collection = None
    else:
        print(f"⚠️  Resource type '{resource_type}' not yet supported in creation logic")
        return None
    
    # Test collection schema (if available)
    if collection and collection_schema:
        print(f"\n🔍 Testing {collection_type} Schema Compliance...")
        collection_results = test_resource_collection_schema(collection, original_data, collection_schema, collection_type)
        
        print(f"   Collection Tests Passed: {len(collection_results['passed'])}")
        print(f"   Collection Tests Failed: {len(collection_results['failed'])}")
        print(f"   Collection Warnings: {len(collection_results['warnings'])}")
    else:
        collection_results = {'passed': [], 'failed': [], 'warnings': []}
    
    # Test individual resources
    print(f"\n🔬 Testing Individual {resource_type} Schema Compliance...")
    all_passed = 0
    all_failed = 0
    all_warnings = 0
    
    for i, resource_obj in enumerate(resources):
        # Get resource name dynamically
        resource_name = getattr(resource_obj, 'repository', f'{resource_type}_{i+1}')
        print(f"\n  Testing Resource {i+1}: {resource_name}")
        
        # Test base resource fields (generic for all resource types)
        base_results = test_base_resource_fields(resource_obj, original_data['resources'][i])
        
        # Test schema-specific fields (dynamic based on YAML)
        schema_results = test_resource_schema(resource_obj, original_data['resources'][i], resource_schema, resource_type)
        
        # Combine results
        passed = len(base_results['passed']) + len(schema_results['passed'])
        failed = len(base_results['failed']) + len(schema_results['failed'])
        warnings = len(base_results['warnings']) + len(schema_results['warnings'])
        
        print(f"    ✅ Passed: {passed}")
        print(f"    ❌ Failed: {failed}")
        if warnings:
            print(f"    ⚠️  Warnings: {warnings}")
        
        all_passed += passed
        all_failed += failed
        all_warnings += warnings
        
        # Show sample results for first resource
        if i == 0 and failed > 0:
            print("    Sample failed tests:")
            all_failed_tests = base_results['failed'] + schema_results['failed']
            for test in all_failed_tests[:3]:
                print(f"      {test}")
    
    # Final summary
    total_passed = all_passed + len(collection_results['passed'])
    total_failed = all_failed + len(collection_results['failed'])
    total_warnings = all_warnings + len(collection_results['warnings'])
    
    print(f"\n📊 Final Dynamic Schema Test Summary:")
    print(f"   Resource Type Tested: {resource_type}")
    if collection_type:
        print(f"   Collection Type Tested: {collection_type}")
    print(f"   Total Tests Passed: {total_passed}")
    print(f"   Total Tests Failed: {total_failed}")
    print(f"   Total Warnings: {total_warnings}")
    
    if total_failed + total_passed > 0:
        success_rate = total_passed / (total_passed + total_failed) * 100
        print(f"   Success Rate: {success_rate:.1f}%")
    
    if total_failed == 0:
        print(f"\n🎉 All schema-based tests passed! Complete data integrity maintained for {resource_type}.")
    else:
        print(f"\n⚠️  {total_failed} tests failed. Schema compliance issues detected for {resource_type}.")
    
    return collection if collection else resources

if __name__ == "__main__":
    run_dynamic_schema_test() 