#!/usr/bin/env python3
"""
System integration test - combines checks and resources for end-to-end testing.
Imports checks, runs them against resources, and returns enriched resources with check results.
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Import our modules
import checks
import resources
from resources import GithubResource, GithubResourceCollection
from checks.models import CheckResult

@dataclass
class SystemTestResult:
    """Result of running the complete system test."""
    resources: GithubResourceCollection
    check_results: List[CheckResult]
    total_checks_run: int
    checks_passed: int
    checks_failed: int
    success_rate: float
    execution_time: float

def load_and_create_resources() -> GithubResourceCollection:
    """Load response.json and create GithubResourceCollection."""
    
    print("📂 Loading response.json...")
    with open('response.json', 'r') as f:
        response_data = json.load(f)
    
    print(f"✅ Loaded data for {len(response_data['resources'])} resources")
    
    # Create GithubResource instances
    github_resources = []
    
    for resource_data in response_data['resources']:
        # Extract GitHub repository metadata from data.metadata
        github_repo_metadata = resource_data['data'].get('metadata', {})
        
        github_resource = GithubResource(
            id=resource_data['id'],
            source_connector=resource_data['source_connector'],
            created_at=datetime.fromisoformat(resource_data['created_at']),
            updated_at=datetime.fromisoformat(resource_data['updated_at']),
            metadata=github_repo_metadata,
            tags=resource_data.get('tags', []),
            
            # Schema-specific fields
            repository=resource_data['data']['repository'],
            basic_info=resource_data['data']['basic_info'],
            branches=resource_data['data']['branches'],
            statistics=resource_data['data']['statistics']
        )
        
        # Preserve original resource metadata in tags
        original_resource_metadata = resource_data.get('metadata', {})
        if original_resource_metadata:
            if 'authenticated_user' in original_resource_metadata:
                github_resource.add_tag(f"user:{original_resource_metadata['authenticated_user']}")
            if 'provider' in original_resource_metadata:
                github_resource.add_tag(f"provider:{original_resource_metadata['provider']}")
        
        # Add a data property for backwards compatibility with checks
        @property
        def data_property(self):
            """Backwards compatibility property that mimics the old data structure."""
            return {
                'repository': self.repository,
                'basic_info': self.basic_info,
                'metadata': self.metadata,
                'branches': self.branches,
                'statistics': self.statistics
            }
        
        # Monkey patch the data property onto the resource
        github_resource.__class__.data = data_property
        
        github_resources.append(github_resource)
    
    # Create collection
    collection = GithubResourceCollection(
        resources=github_resources,
        source_connector='github',
        total_count=len(github_resources),
        fetched_at=datetime.now().isoformat(),
        collection_metadata={
            'authenticated_user': 'vishesh-kovr',
            'total_repositories': len(github_resources),
            'system_test': True
        },
        github_api_metadata={
            'collection_time': datetime.now().isoformat(),
            'api_version': 'v3',
            'test_mode': True
        }
    )
    
    print(f"✅ Created GithubResourceCollection with {len(collection)} resources")
    return collection

def run_checks_against_resources(collection: GithubResourceCollection) -> List[CheckResult]:
    """Run all available checks against the resource collection."""
    
    print("\n🔍 Loading and running checks...")
    
    # Get all loaded checks
    loaded_checks = checks.get_loaded_checks()
    print(f"📋 Found {len(loaded_checks)} available checks:")
    
    for check_name, check_obj in loaded_checks.items():
        print(f"   - {check_name}: {check_obj.description}")
    
    # Convert GithubResource objects to generic Resource objects for compatibility
    from resources.models import Resource
    generic_resources = []
    
    for github_resource in collection.resources:
        # Convert metadata to dict if it's a Pydantic model
        if hasattr(github_resource.metadata, '__dict__'):
            metadata_dict = github_resource.metadata.__dict__
        elif hasattr(github_resource.metadata, 'dict'):
            metadata_dict = github_resource.metadata.dict()
        else:
            metadata_dict = github_resource.metadata if isinstance(github_resource.metadata, dict) else {}
        
        # Convert to generic Resource format
        generic_resource = Resource(
            id=github_resource.id,
            source_connector=github_resource.source_connector,
            data={
                'repository': github_resource.repository,
                'basic_info': github_resource.basic_info.__dict__ if hasattr(github_resource.basic_info, '__dict__') else github_resource.basic_info,
                'metadata': metadata_dict,
                'branches': [
                    branch.__dict__ if hasattr(branch, '__dict__') else branch 
                    for branch in github_resource.branches
                ],
                'statistics': github_resource.statistics.__dict__ if hasattr(github_resource.statistics, '__dict__') else github_resource.statistics
            },
            created_at=github_resource.created_at,
            updated_at=github_resource.updated_at,
            metadata=metadata_dict,
            tags=github_resource.tags
        )
        generic_resources.append(generic_resource)
    
    print(f"✅ Converted {len(generic_resources)} GithubResource objects to generic Resource format")
    
    # Run checks against all resources
    all_check_results = []
    
    for check_name, check_obj in loaded_checks.items():
        print(f"\n🔄 Running check: {check_name}")
        
        try:
            # Run check against generic resources
            check_results = check_obj.evaluate(generic_resources)
            all_check_results.extend(check_results)
            
            # Display results
            passed_count = sum(1 for r in check_results if r.passed)
            failed_count = len(check_results) - passed_count
            
            print(f"   ✅ Passed: {passed_count}")
            print(f"   ❌ Failed: {failed_count}")
            
            # Show details for each resource
            for result in check_results:
                status_icon = "✅" if result.passed else "❌"
                repo_name = result.resource.get_field_value('repository')
                print(f"      {status_icon} {repo_name}: {result.message}")
                
        except Exception as e:
            print(f"   ❌ Error running check {check_name}: {str(e)}")
    
    return all_check_results

def enrich_resources_with_check_results(collection: GithubResourceCollection, check_results: List[CheckResult]) -> GithubResourceCollection:
    """Enrich resources with check results metadata."""
    
    print(f"\n📊 Enriching resources with check results...")
    
    # Group check results by resource
    results_by_resource = {}
    for result in check_results:
        resource_id = result.resource.id
        if resource_id not in results_by_resource:
            results_by_resource[resource_id] = []
        results_by_resource[resource_id].append(result)
    
    # Add check results to each resource's metadata
    for resource in collection.resources:
        resource_results = results_by_resource.get(resource.id, [])
        
        # Add check results summary to metadata - handle Pydantic model vs dict
        try:
            # Try to add to metadata if it's a dict-like object
            if hasattr(resource.metadata, '__dict__'):
                # It's a Pydantic model, we can set attributes directly
                setattr(resource.metadata, 'check_results_total', len(resource_results))
                setattr(resource.metadata, 'check_results_passed', sum(1 for r in resource_results if r.passed))
                setattr(resource.metadata, 'check_results_failed', sum(1 for r in resource_results if not r.passed))
                setattr(resource.metadata, 'check_results_success_rate', 
                       (sum(1 for r in resource_results if r.passed) / len(resource_results) * 100) if resource_results else 0)
            elif isinstance(resource.metadata, dict):
                # It's a dictionary
                resource.metadata['check_results'] = {
                    'total_checks': len(resource_results),
                    'checks_passed': sum(1 for r in resource_results if r.passed),
                    'checks_failed': sum(1 for r in resource_results if not r.passed),
                    'success_rate': (sum(1 for r in resource_results if r.passed) / len(resource_results) * 100) if resource_results else 0,
                    'check_details': [
                        {
                            'check_name': r.check.name,
                            'passed': r.passed,
                            'message': r.message
                        } for r in resource_results
                    ]
                }
        except Exception as e:
            print(f"⚠️  Could not add check results to metadata for {resource.id}: {e}")
        
        # Add tags for check results
        if resource_results:
            passed_count = sum(1 for r in resource_results if r.passed)
            failed_count = len(resource_results) - passed_count
            
            resource.add_tag(f"checks_passed:{passed_count}")
            resource.add_tag(f"checks_failed:{failed_count}")
            
            if failed_count == 0:
                resource.add_tag("all_checks_passed")
            elif passed_count == 0:
                resource.add_tag("all_checks_failed")
            else:
                resource.add_tag("mixed_check_results")
    
    print(f"✅ Enriched {len(collection.resources)} resources with check results")
    return collection

def run_system_test() -> SystemTestResult:
    """Run the complete system test."""
    
    print("🚀 System Integration Test")
    print("=" * 50)
    
    start_time = datetime.now()
    
    try:
        # Step 1: Load and create resources
        collection = load_and_create_resources()
        
        # Step 2: Run checks against resources
        check_results = run_checks_against_resources(collection)
        
        # Step 3: Enrich resources with check results
        enriched_collection = enrich_resources_with_check_results(collection, check_results)
        
        # Calculate metrics
        total_checks = len(check_results)
        checks_passed = sum(1 for r in check_results if r.passed)
        checks_failed = total_checks - checks_passed
        success_rate = (checks_passed / total_checks * 100) if total_checks > 0 else 0
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        # Create result
        result = SystemTestResult(
            resources=enriched_collection,
            check_results=check_results,
            total_checks_run=total_checks,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            success_rate=success_rate,
            execution_time=execution_time
        )
        
        # Display final summary
        print(f"\n📈 System Test Summary:")
        print(f"   Resources processed: {len(enriched_collection)}")
        print(f"   Total checks run: {total_checks}")
        print(f"   Checks passed: {checks_passed}")
        print(f"   Checks failed: {checks_failed}")
        print(f"   Success rate: {success_rate:.1f}%")
        print(f"   Execution time: {execution_time:.2f}s")
        
        if checks_failed == 0:
            print(f"\n🎉 All system checks passed!")
        else:
            print(f"\n⚠️  System has {checks_failed} failing checks")
        
        print(f"\n💾 Returning enriched resource collection with check results")
        
        return result
        
    except Exception as e:
        print(f"\n❌ System test failed with error: {str(e)}")
        raise

def display_detailed_results(result: SystemTestResult):
    """Display detailed results of the system test."""
    
    print(f"\n📋 Detailed Results:")
    print(f"=" * 30)
    
    for i, resource in enumerate(result.resources.resources, 1):
        print(f"\n{i}. {resource.repository}")
        
        # Show resource info
        basic_info = resource.basic_info
        if isinstance(basic_info, dict):
            language = basic_info.get('language', 'Unknown')
            private = basic_info.get('private', 'Unknown')
        else:
            language = getattr(basic_info, 'language', 'Unknown')
            private = getattr(basic_info, 'private', 'Unknown')
            
        print(f"   Language: {language}")
        print(f"   Private: {private}")
        print(f"   Branches: {len(resource.branches)}")
        
        # Show check results - handle both dict and Pydantic model metadata
        try:
            if hasattr(resource.metadata, 'check_results_total'):
                # Pydantic model with check results
                total = getattr(resource.metadata, 'check_results_total', 0)
                passed = getattr(resource.metadata, 'check_results_passed', 0)
                success_rate = getattr(resource.metadata, 'check_results_success_rate', 0)
                
                if total > 0:
                    print(f"   Checks: {passed}/{total} passed ({success_rate:.1f}%)")
                else:
                    print(f"   Checks: No checks run")
                    
            elif isinstance(resource.metadata, dict) and 'check_results' in resource.metadata:
                # Dictionary metadata with check results
                check_meta = resource.metadata['check_results']
                print(f"   Checks: {check_meta['checks_passed']}/{check_meta['total_checks']} passed ({check_meta['success_rate']:.1f}%)")
                
                for check_detail in check_meta['check_details'][:3]:  # Show first 3 checks
                    status = "✅" if check_detail['passed'] else "❌"
                    print(f"      {status} {check_detail['check_name']}: {check_detail['message']}")
            else:
                # Check tags for check results
                check_tags = [tag for tag in resource.tags if tag.startswith('checks_')]
                if check_tags:
                    print(f"   Check tags: {', '.join(check_tags)}")
                else:
                    print(f"   Checks: No check results available")
                    
        except Exception as e:
            print(f"   Checks: Error accessing check results - {e}")

def main():
    """Main function to run the system test."""
    
    # Run the system test
    result = run_system_test()
    
    # Display detailed results
    display_detailed_results(result)
    
    return result

if __name__ == "__main__":
    system_result = main() 