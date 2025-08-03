#!/usr/bin/env python3
"""
Test resources module - verify GithubResourceCollection and GithubResource models
contain all data from response.json without data loss.
"""

import json
from datetime import datetime
from typing import Any, Dict, List
from resources import GithubResource, GithubResourceCollection

def load_response_data() -> Dict[str, Any]:
    """Load the response.json file."""
    with open('response.json', 'r') as f:
        return json.load(f)

def create_github_resources_from_response(response_data: Dict[str, Any]) -> List[GithubResource]:
    """Create GithubResource objects from response data."""
    github_resources = []
    
    for resource_data in response_data['resources']:
        # Extract GitHub repository metadata from data.metadata
        github_repo_metadata = resource_data['data'].get('metadata', {})
        
        github_resource = GithubResource(
            id=resource_data['id'],
            source_connector=resource_data['source_connector'],
            created_at=datetime.fromisoformat(resource_data['created_at']),
            updated_at=datetime.fromisoformat(resource_data['updated_at']),
            metadata=github_repo_metadata,  # Use GitHub repository metadata for the metadata field
            tags=resource_data.get('tags', []),
            
            # Schema-specific fields from the data section
            repository=resource_data['data']['repository'],
            basic_info=resource_data['data']['basic_info'],
            branches=resource_data['data']['branches'],
            statistics=resource_data['data']['statistics']
        )
        
        # Store original resource metadata in a custom way if needed
        # We could add this to tags or handle it differently
        original_resource_metadata = resource_data.get('metadata', {})
        if original_resource_metadata:
            # Add resource metadata info as tags for tracking
            if 'authenticated_user' in original_resource_metadata:
                github_resource.add_tag(f"user:{original_resource_metadata['authenticated_user']}")
            if 'provider' in original_resource_metadata:
                github_resource.add_tag(f"provider:{original_resource_metadata['provider']}")
        
        github_resources.append(github_resource)
    
    return github_resources

def create_github_resource_collection(github_resources: List[GithubResource]) -> GithubResourceCollection:
    """Create a GithubResourceCollection from GithubResource objects."""
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

def test_data_completeness(original_data: Dict[str, Any], github_resource: GithubResource, resource_index: int) -> Dict[str, List[str]]:
    """Test if all data from original JSON is accessible in the GithubResource model."""
    
    results = {
        'passed': [],
        'failed': [],
        'warnings': []
    }
    
    original_resource = original_data['resources'][resource_index]
    original_data_section = original_resource['data']
    
    # Test base resource fields (excluding metadata and tags which need special handling)
    base_fields = ['id', 'source_connector', 'created_at', 'updated_at']
    for field in base_fields:
        try:
            model_value = getattr(github_resource, field)
            original_value = original_resource[field]
            
            # Special handling for datetime fields
            if field in ['created_at', 'updated_at']:
                if isinstance(model_value, datetime):
                    model_value = model_value.isoformat()
                if model_value == original_value:
                    results['passed'].append(f"✅ {field}: {model_value}")
                else:
                    results['failed'].append(f"❌ {field}: Expected {original_value}, got {model_value}")
            else:
                if model_value == original_value:
                    results['passed'].append(f"✅ {field}: matches")
                else:
                    results['failed'].append(f"❌ {field}: Expected {original_value}, got {model_value}")
        except Exception as e:
            results['failed'].append(f"❌ {field}: Error accessing - {str(e)}")
    
    # Test tags field - should contain original tags plus additional metadata preservation tags
    original_tags = original_resource['tags']
    try:
        model_tags = github_resource.tags
        
        # Check that all original tags are present
        original_tags_present = all(tag in model_tags for tag in original_tags)
        if original_tags_present:
            results['passed'].append(f"✅ tags: All original tags present ({len(original_tags)} tags)")
        else:
            missing_tags = [tag for tag in original_tags if tag not in model_tags]
            results['failed'].append(f"❌ tags: Missing original tags: {missing_tags}")
        
        # Check for expected additional tags (resource metadata preservation)
        original_resource_metadata = original_resource.get('metadata', {})
        if original_resource_metadata:
            expected_user_tag = f"user:{original_resource_metadata.get('authenticated_user', '')}"
            expected_provider_tag = f"provider:{original_resource_metadata.get('provider', '')}"
            
            if expected_user_tag in model_tags:
                results['passed'].append(f"✅ tags: Resource metadata user tag present")
            else:
                results['failed'].append(f"❌ tags: Expected user tag {expected_user_tag} not found")
                
            if expected_provider_tag in model_tags:
                results['passed'].append(f"✅ tags: Resource metadata provider tag present")  
            else:
                results['failed'].append(f"❌ tags: Expected provider tag {expected_provider_tag} not found")
    except Exception as e:
        results['failed'].append(f"❌ tags: Error accessing - {str(e)}")
    
    # Test metadata field - should contain GitHub repository metadata, not resource metadata
    original_github_metadata = original_data_section['metadata']
    try:
        model_metadata = github_resource.metadata
        metadata_fields = ['default_branch', 'topics', 'has_issues', 'has_projects', 'has_wiki', 
                          'has_pages', 'has_downloads', 'has_discussions', 'is_template', 'license']
        
        for field in metadata_fields:
            try:
                if isinstance(model_metadata, dict):
                    model_value = model_metadata.get(field)
                else:
                    model_value = getattr(model_metadata, field, None)
                
                original_value = original_github_metadata.get(field)
                
                if model_value == original_value:
                    results['passed'].append(f"✅ metadata.{field}: matches")
                else:
                    results['failed'].append(f"❌ metadata.{field}: Expected {original_value}, got {model_value}")
            except Exception as e:
                results['failed'].append(f"❌ metadata.{field}: Error accessing - {str(e)}")
    except Exception as e:
        results['failed'].append(f"❌ metadata: Error accessing - {str(e)}")
    
    # Test data section fields
    
    # Test repository field
    try:
        if github_resource.repository == original_data_section['repository']:
            results['passed'].append(f"✅ repository: {github_resource.repository}")
        else:
            results['failed'].append(f"❌ repository: Expected {original_data_section['repository']}, got {github_resource.repository}")
    except Exception as e:
        results['failed'].append(f"❌ repository: Error accessing - {str(e)}")
    
    # Test basic_info fields
    original_basic_info = original_data_section['basic_info']
    try:
        model_basic_info = github_resource.basic_info
        basic_info_fields = ['id', 'name', 'full_name', 'description', 'private', 'owner', 
                           'html_url', 'clone_url', 'ssh_url', 'size', 'language', 
                           'created_at', 'updated_at', 'pushed_at', 'stargazers_count',
                           'watchers_count', 'forks_count', 'open_issues_count', 'archived', 'disabled']
        
        for field in basic_info_fields:
            try:
                if isinstance(model_basic_info, dict):
                    model_value = model_basic_info.get(field)
                else:
                    model_value = getattr(model_basic_info, field, None)
                
                original_value = original_basic_info.get(field)
                
                if model_value == original_value:
                    results['passed'].append(f"✅ basic_info.{field}: matches")
                else:
                    results['failed'].append(f"❌ basic_info.{field}: Expected {original_value}, got {model_value}")
            except Exception as e:
                results['failed'].append(f"❌ basic_info.{field}: Error accessing - {str(e)}")
    except Exception as e:
        results['failed'].append(f"❌ basic_info: Error accessing - {str(e)}")
    
    # Test branches
    original_branches = original_data_section['branches']
    try:
        model_branches = github_resource.branches
        if len(model_branches) == len(original_branches):
            results['passed'].append(f"✅ branches: {len(model_branches)} branches present")
            
            # Test first branch in detail if available
            if model_branches and original_branches:
                first_branch = model_branches[0]
                first_original = original_branches[0]
                
                branch_fields = ['name', 'sha', 'protected', 'protection_details']
                for field in branch_fields:
                    try:
                        if isinstance(first_branch, dict):
                            model_value = first_branch.get(field)
                        else:
                            model_value = getattr(first_branch, field, None)
                        
                        original_value = first_original.get(field)
                        
                        if model_value == original_value:
                            results['passed'].append(f"✅ branches[0].{field}: matches")
                        else:
                            results['failed'].append(f"❌ branches[0].{field}: Expected {original_value}, got {model_value}")
                    except Exception as e:
                        results['failed'].append(f"❌ branches[0].{field}: Error accessing - {str(e)}")
        else:
            results['failed'].append(f"❌ branches: Expected {len(original_branches)} branches, got {len(model_branches)}")
    except Exception as e:
        results['failed'].append(f"❌ branches: Error accessing - {str(e)}")
    
    # Test statistics
    original_statistics = original_data_section['statistics']
    try:
        model_statistics = github_resource.statistics
        stats_fields = ['total_commits', 'contributors_count', 'languages', 'code_frequency']
        
        for field in stats_fields:
            try:
                if isinstance(model_statistics, dict):
                    model_value = model_statistics.get(field)
                else:
                    model_value = getattr(model_statistics, field, None)
                
                original_value = original_statistics.get(field)
                
                if model_value == original_value:
                    results['passed'].append(f"✅ statistics.{field}: matches")
                else:
                    results['failed'].append(f"❌ statistics.{field}: Expected {original_value}, got {model_value}")
            except Exception as e:
                results['failed'].append(f"❌ statistics.{field}: Error accessing - {str(e)}")
    except Exception as e:
        results['failed'].append(f"❌ statistics: Error accessing - {str(e)}")
    
    return results

def test_collection_functionality(collection: GithubResourceCollection, original_data: Dict[str, Any]) -> Dict[str, List[str]]:
    """Test GithubResourceCollection functionality."""
    
    results = {
        'passed': [],
        'failed': [],
        'warnings': []
    }
    
    # Test collection basic properties
    try:
        if len(collection) == len(original_data['resources']):
            results['passed'].append(f"✅ Collection length: {len(collection)}")
        else:
            results['failed'].append(f"❌ Collection length: Expected {len(original_data['resources'])}, got {len(collection)}")
    except Exception as e:
        results['failed'].append(f"❌ Collection length: Error - {str(e)}")
    
    # Test collection iteration
    try:
        count = 0
        for resource in collection:
            if isinstance(resource, GithubResource):
                count += 1
            else:
                results['failed'].append(f"❌ Iteration: Item {count} is not GithubResource, got {type(resource)}")
        
        if count == len(original_data['resources']):
            results['passed'].append(f"✅ Collection iteration: All {count} items are GithubResource objects")
        else:
            results['failed'].append(f"❌ Collection iteration: Expected {len(original_data['resources'])}, iterated {count}")
    except Exception as e:
        results['failed'].append(f"❌ Collection iteration: Error - {str(e)}")
    
    # Test collection indexing
    try:
        first_resource = collection[0]
        if isinstance(first_resource, GithubResource):
            results['passed'].append(f"✅ Collection indexing: collection[0] returns GithubResource")
        else:
            results['failed'].append(f"❌ Collection indexing: collection[0] returned {type(first_resource)}")
    except Exception as e:
        results['failed'].append(f"❌ Collection indexing: Error - {str(e)}")
    
    # Test collection metadata
    try:
        if hasattr(collection, 'collection_metadata'):
            results['passed'].append(f"✅ Collection metadata: Available")
        else:
            results['failed'].append(f"❌ Collection metadata: Not available")
    except Exception as e:
        results['failed'].append(f"❌ Collection metadata: Error - {str(e)}")
    
    return results

def run_comprehensive_test():
    """Run comprehensive test of resources module."""
    
    print("🧪 Comprehensive Resources Test")
    print("=" * 50)
    
    # Load original data
    print("📂 Loading response.json...")
    original_data = load_response_data()
    print(f"✅ Loaded data for {len(original_data['resources'])} resources")
    
    # Create GithubResource objects
    print("\n🏗️  Creating GithubResource objects...")
    github_resources = create_github_resources_from_response(original_data)
    print(f"✅ Created {len(github_resources)} GithubResource objects")
    
    # Create GithubResourceCollection
    print("\n📦 Creating GithubResourceCollection...")
    collection = create_github_resource_collection(github_resources)
    print(f"✅ Created collection with {len(collection)} resources")
    
    # Test collection functionality
    print("\n🔍 Testing Collection Functionality...")
    collection_results = test_collection_functionality(collection, original_data)
    
    print(f"   Collection Tests Passed: {len(collection_results['passed'])}")
    print(f"   Collection Tests Failed: {len(collection_results['failed'])}")
    if collection_results['warnings']:
        print(f"   Collection Warnings: {len(collection_results['warnings'])}")
    
    # Test individual resources
    print("\n🔬 Testing Individual Resources...")
    all_passed = 0
    all_failed = 0
    all_warnings = 0
    
    for i, github_resource in enumerate(collection.resources):
        print(f"\n  Testing Resource {i+1}: {github_resource.repository}")
        resource_results = test_data_completeness(original_data, github_resource, i)
        
        passed = len(resource_results['passed'])
        failed = len(resource_results['failed'])
        warnings = len(resource_results['warnings'])
        
        print(f"    ✅ Passed: {passed}")
        print(f"    ❌ Failed: {failed}")
        if warnings:
            print(f"    ⚠️  Warnings: {warnings}")
        
        all_passed += passed
        all_failed += failed
        all_warnings += warnings
        
        # Show some details for first resource
        if i == 0:
            print("    Sample passed tests:")
            for test in resource_results['passed'][:5]:
                print(f"      {test}")
            
            if resource_results['failed']:
                print("    Failed tests:")
                for test in resource_results['failed'][:3]:
                    print(f"      {test}")
    
    # Final summary
    print(f"\n📊 Final Summary:")
    print(f"   Total Tests Passed: {all_passed + len(collection_results['passed'])}")
    print(f"   Total Tests Failed: {all_failed + len(collection_results['failed'])}")
    print(f"   Total Warnings: {all_warnings + len(collection_results['warnings'])}")
    
    success_rate = (all_passed + len(collection_results['passed'])) / (all_passed + all_failed + len(collection_results['passed']) + len(collection_results['failed'])) * 100
    print(f"   Success Rate: {success_rate:.1f}%")
    
    if all_failed + len(collection_results['failed']) == 0:
        print("\n🎉 All tests passed! Data integrity maintained.")
    else:
        print(f"\n⚠️  Some tests failed. Data completeness issues detected.")
    
    return collection

if __name__ == "__main__":
    run_comprehensive_test() 