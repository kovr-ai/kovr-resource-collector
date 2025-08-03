#!/usr/bin/env python3
"""
Test simplified checks implementation by running available checks against real data.
"""

import json
import checks
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class CheckResult:
    """Result of running a check against a resource."""
    passed: bool
    check_name: str
    resource_name: str
    message: str
    error: str = None

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

def run_available_checks():
    """Load data and run all available checks against it."""
    
    print("=== Running Available Checks Against Real Data ===\n")
    
    # Load real GitHub data
    print("📂 Loading GitHub data...")
    response_data = load_response_data()
    if not response_data:
        return False
    
    repositories_data = response_data.get('repositories_data', [])
    print(f"✅ Loaded {len(repositories_data)} repositories\n")
    
    # Get all loaded checks
    loaded_checks = checks.get_loaded_checks()
    print(f"🔍 Found {len(loaded_checks)} available checks:")
    for check_name, check_config in loaded_checks.items():
        print(f"   - {check_name}: {check_config['description']}")
    print()
    
    # Run all checks and collect results
    all_check_results: List[CheckResult] = []
    
    for check_name, check_config in loaded_checks.items():
        print(f"🔍 Running check: {check_name}")
        
        for repo_data in repositories_data:
            repo_name = repo_data.get('repository', 'unknown')
            
            # Run the check and create CheckResult
            result = evaluate_check_with_result(check_config, check_name, repo_data, repo_name)
            all_check_results.append(result)
            
            # Display result
            status_icon = "✅" if result.passed else "❌"
            print(f"   {status_icon} {repo_name}: {result.message}")
        
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
            resources = [r.resource_name for r in results]
            print(f"   {check_name}: {', '.join(resources)}")
    else:
        print("   None")
    
    print(f"\n❌ FAILED CHECKS ({len(failed_results)}):")
    if failed_results:
        grouped_failed = group_results_by_check(failed_results)
        for check_name, results in grouped_failed.items():
            resources = [r.resource_name for r in results]
            print(f"   {check_name}: {', '.join(resources)}")
    else:
        print("   None")
    
    # Overall summary
    print(f"\n=== Overall Summary ===")
    print(f"Total checks run: {len(all_check_results)}")
    print(f"✅ Total passed: {len(passed_results)}")
    print(f"❌ Total failed: {len(failed_results)}")
    
    if len(failed_results) == 0:
        print("🎉 All checks passed!")
    elif len(passed_results) == 0:
        print("⚠️  All checks failed!")
    else:
        success_rate = (len(passed_results) / len(all_check_results)) * 100
        print(f"📊 Success rate: {success_rate:.1f}%")
    
    return True

def evaluate_check_with_result(check_config: Dict[str, Any], check_name: str, repo_data: Dict[str, Any], repo_name: str) -> CheckResult:
    """Evaluate a single check against repository data and return CheckResult."""
    check_method = check_config.get('check_method')
    expected_value = check_config.get('expected_value')
    
    try:
        if check_method == 'is_all_branches_protected':
            # Check if all branches are protected
            branches = repo_data.get('branches', [])
            if not branches:
                return CheckResult(
                    passed=False,
                    check_name=check_name,
                    resource_name=repo_name,
                    message="No branches found",
                    error="Repository has no branches"
                )
            
            all_protected = all(branch.get('protected', False) for branch in branches)
            protected_count = sum(1 for b in branches if b.get('protected', False))
            
            return CheckResult(
                passed=all_protected,
                check_name=check_name,
                resource_name=repo_name,
                message=f"Branch protection: {protected_count}/{len(branches)} protected"
            )
        
        # Add more check method handlers here as needed
        return CheckResult(
            passed=False,
            check_name=check_name,
            resource_name=repo_name,
            message="Unknown check method",
            error=f"Unknown check method: {check_method}"
        )
        
    except Exception as e:
        return CheckResult(
            passed=False,
            check_name=check_name,
            resource_name=repo_name,
            message="Check execution failed",
            error=str(e)
        )

def group_results_by_check(results: List[CheckResult]) -> Dict[str, List[CheckResult]]:
    """Group CheckResults by check name."""
    grouped = {}
    for result in results:
        if result.check_name not in grouped:
            grouped[result.check_name] = []
        grouped[result.check_name].append(result)
    return grouped

if __name__ == "__main__":
    run_available_checks() 