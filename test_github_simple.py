#!/usr/bin/env python3
"""
Simple GitHub workflow test - step by step.

Step 1: Call GitHub service
Step 2: Get GithubResourceCollection directly 
Step 3: Run checks
Step 4: Show results
"""

import os
from connectors import github, GithubConnectorInput
from resources import GithubResourceCollection

def main():
    print("🚀 GitHub Simple Workflow Test")
    print("=" * 40)
    
    # Step 1: Call GitHub service
    print("\n📡 Step 1: Calling GitHub service...")
    
    input_config = GithubConnectorInput(
        token=os.getenv('GITHUB_TOKEN', 'dummy_token'),
        org_name='kovr-ai',
        mini_run=1,
        repositories_limit=5
    )
    
    print(f"   Input: org='{input_config.org_name}', mini_run={input_config.mini_run}")
    
    # Step 2: Get GithubResourceCollection directly
    print("\n📊 Step 2: Fetching GithubResourceCollection...")
    result = github.fetch_data(input_config)
    print(f"   ✅ Got result: {type(result)}")
    print(f"   Expected type: GithubResourceCollection")
    
    # Step 3: Inspect the resource collection
    print("\n🏗️ Step 3: Inspecting resource collection...")
    
    if isinstance(result, GithubResourceCollection):
        resources = result.resources
        print(f"   ✅ GithubResourceCollection with {len(resources)} resources")
        
        if resources:
            first_resource = resources[0]
            print(f"   First resource: {first_resource.repository}")
            print(f"   Resource type: {type(first_resource)}")
        else:
            print("   ❌ No resources in collection")
    else:
        print(f"   ❌ Expected GithubResourceCollection, got {type(result)}")
        return
    
    # Step 4: Summary
    print("\n🎯 Step 4: Summary...")
    print(f"   ✅ GitHub service returns GithubResourceCollection directly")
    print(f"   ✅ Collection contains {len(resources)} GitHub resources")
    print("   📝 Ready for checks system!")

if __name__ == "__main__":
    main() 