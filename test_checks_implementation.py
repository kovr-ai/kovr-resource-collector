#!/usr/bin/env python3
"""
Test simplified checks implementation by running available checks against real data.
"""

import json
import checks
from typing import List, Dict, Any
from checks.models import CheckResult as ChecksCheckResult
from resources.models import Resource, ResourceCollection
from datetime import datetime

def load_response_data(file_path: str = "response.json"):
    """Load the response.json file."""
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON: {e}")
        return None

def create_resources_from_response_data(response_data: Dict[str, Any]) -> List[Resource]:
    """Convert response data to Resource objects."""
    resources_list = []
    
    # This is already processed resource data
    for resource_data in response_data['resources']:
        # Create Resource instance from the processed data
        resource = Resource(
            id=resource_data['id'],
            source_connector=resource_data['source_connector'],
            data=resource_data['data'],
            created_at=datetime.fromisoformat(resource_data['created_at']),
            updated_at=datetime.fromisoformat(resource_data['updated_at']),
            metadata=resource_data.get('metadata', {}),
            tags=resource_data.get('tags', [])
        )
        resources_list.append(resource)
    
    return resources_list

def run_available_checks():
    """Load data and run all available checks against it."""
    
    print("=== Running Available Checks Against Real Data ===\n")
    
    # Load GitHub data from response.json
    print("📂 Loading GitHub data from response.json...")
    response_data = load_response_data()
    if not response_data:
        return False
    
    # Convert to Resource objects
    resources_list = create_resources_from_response_data(response_data)
    print(f"✅ Loaded {len(resources_list)} repositories as Resource objects\n")
    
    # Get all loaded checks
    loaded_checks = checks.get_loaded_checks()
    print(f"🔍 Found {len(loaded_checks)} available checks:")
    for check_name, check_obj in loaded_checks.items():
        print(f"   - {check_name}: {check_obj.description or 'No description'}")
    print()
    
    # Run all checks and collect results
    all_check_results: List[ChecksCheckResult] = []
    
    for check_name, check_obj in loaded_checks.items():
        print(f"🔍 Running check: {check_name}")
        
        # Run the check against all resources
        try:
            check_results = check_obj.evaluate(resources_list)
            all_check_results.extend(check_results)
            
            # Display results for this check
            for result in check_results:
                status_icon = "✅" if result.passed else "❌"
                repo_name = result.resource.get_field_value('repository')
                print(f"   {status_icon} {repo_name}: {result.message}")
                
        except Exception as e:
            print(f"   ❌ Error running check {check_name}: {str(e)}")
        
        print()
    
    # Group results by success/failure
    passed_results = [r for r in all_check_results if r.passed]
    failed_results = [r for r in all_check_results if not r.passed]
    
    # Display grouped results
    print("=== Grouped Results ===")
    
    print(f"\n✅ PASSED CHECKS ({len(passed_results)}):")
    if passed_results:
        grouped_passed = group_results_by_check(passed_results)
        for check_name, results in grouped_passed.items():
            resources = [r.resource.get_field_value('repository') for r in results]
            print(f"   {check_name}: {', '.join(resources)}")
    else:
        print("   None")
    
    print(f"\n❌ FAILED CHECKS ({len(failed_results)}):")
    if failed_results:
        grouped_failed = group_results_by_check(failed_results)
        for check_name, results in grouped_failed.items():
            resources = [r.resource.get_field_value('repository') for r in results]
            print(f"   {check_name}: {', '.join(resources)}")
    else:
        print("   None")
    
    # Overall summary
    print(f"\n=== Overall Summary ===")
    print(f"Total checks run: {len(all_check_results)}")
    print(f"✅ Total passed: {len(passed_results)}")
    print(f"❌ Total failed: {len(failed_results)}")
    
    if len(failed_results) == 0 and len(passed_results) > 0:
        print("🎉 All checks passed!")
    elif len(passed_results) == 0 and len(failed_results) > 0:
        print("⚠️  All checks failed!")
    elif len(all_check_results) > 0:
        success_rate = (len(passed_results) / len(all_check_results)) * 100
        print(f"📊 Success rate: {success_rate:.1f}%")
    else:
        print("ℹ️  No checks were run")
    
    return True

def group_results_by_check(results: List[ChecksCheckResult]) -> Dict[str, List[ChecksCheckResult]]:
    """Group CheckResults by check name."""
    grouped = {}
    for result in results:
        check_name = result.check.name
        if check_name not in grouped:
            grouped[check_name] = []
        grouped[check_name].append(result)
    return grouped

if __name__ == "__main__":
    run_available_checks() 