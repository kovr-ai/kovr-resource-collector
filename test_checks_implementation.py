#!/usr/bin/env python3
"""
Test checks implementation against real response.json data.
"""

import json
import checks
from resources.models import Resource

def load_response_data(file_path: str = "2025-08-02-19-03-26_response.json"):
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

def convert_to_resources(response_data):
    """Convert response data to Resource objects."""
    resources = []
    
    if not response_data or 'repositories_data' not in response_data:
        print("❌ No repositories_data found in response")
        return resources
    
    for repo_data in response_data['repositories_data']:
        try:
            resource = Resource(
                id=repo_data['repository'],
                source_connector="github",
                data=repo_data
            )
            resources.append(resource)
        except Exception as e:
            print(f"❌ Error creating resource for {repo_data.get('repository', 'unknown')}: {e}")
    
    return resources

def run_checks_on_resources():
    """Run all loaded checks against the resources and aggregate results."""
    
    print("=== Testing Checks Implementation Against Real Data ===\n")
    
    # Load real response data
    print("📂 Loading response.json...")
    response_data = load_response_data()
    if not response_data:
        return False
    
    print(f"✅ Loaded data for {response_data.get('total_repositories', 0)} repositories")
    print(f"   Collection time: {response_data.get('collection_time', 'unknown')}")
    print(f"   Authenticated user: {response_data.get('authenticated_user', 'unknown')}\n")
    
    # Convert to Resource objects
    print("🔄 Converting to Resource objects...")
    resources = convert_to_resources(response_data)
    print(f"✅ Created {len(resources)} Resource objects\n")
    
    # Get all loaded checks
    loaded_checks = checks.get_loaded_checks()
    print(f"🔍 Found {len(loaded_checks)} loaded checks:")
    for check_name in loaded_checks.keys():
        print(f"   - {check_name}")
    print()
    
    # Run each check against all resources
    all_results = {}
    
    for check_name, check in loaded_checks.items():
        print(f"🔍 Running check: {check.name}")
        print(f"   Description: {check.description}")
        
        # Run check against all resources
        check_results = check.evaluate(resources)
        all_results[check_name] = check_results
        
        # Count pass/fail for this check
        passed = sum(1 for result in check_results if result.passed)
        failed = sum(1 for result in check_results if not result.passed)
        
        print(f"   ✅ Passed: {passed}/{len(check_results)}")
        print(f"   ❌ Failed: {failed}/{len(check_results)}")
        
        # Show details for each resource
        for result in check_results:
            status_icon = "✅" if result.passed else "❌"
            print(f"     {status_icon} {result.resource.id}: {result.message}")
        
        print()
    
    # Overall summary
    print("=== Overall Summary ===")
    total_check_runs = sum(len(results) for results in all_results.values())
    total_passed = sum(sum(1 for result in results if result.passed) for results in all_results.values())
    total_failed = total_check_runs - total_passed
    
    print(f"Total check executions: {total_check_runs}")
    print(f"✅ Total passed: {total_passed}")
    print(f"❌ Total failed: {total_failed}")
    
    if total_failed == 0:
        print("🎉 All checks passed!")
    elif total_passed == 0:
        print("⚠️  All checks failed!")
    else:
        success_rate = (total_passed / total_check_runs) * 100
        print(f"📊 Success rate: {success_rate:.1f}%")
    
    return True

if __name__ == "__main__":
    run_checks_on_resources() 