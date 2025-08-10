#!/usr/bin/env python3
"""
Test that all imports work correctly across the con_mon_v2 package.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_basic_imports():
    """Test basic package imports."""
    try:
        import con_mon_v2
        print("✅ con_mon_v2 package import successful")
    except Exception as e:
        print(f"❌ con_mon_v2 package import failed: {e}")
        return False
    
    return True

def test_resource_imports():
    """Test resource-related imports."""
    try:
        from con_mon_v2.resources import Resource
        from con_mon_v2.mappings.github import GithubResource
        print("✅ Resource imports successful")
    except Exception as e:
        print(f"❌ Resource imports failed: {e}")
        return False
    
    return True

def test_compliance_imports():
    """Test compliance model imports."""
    try:
        from con_mon_v2.compliance.models import Check, CheckMetadata, OutputStatements, FixDetails
        print("✅ Compliance model imports successful")
    except Exception as e:
        print(f"❌ Compliance model imports failed: {e}")
        return False
    
    return True

def test_llm_imports():
    """Test LLM utility imports."""
    try:
        from con_mon_v2.utils.llm.prompts import ChecksPrompt, generate_checks
        print("✅ LLM utility imports successful")
    except Exception as e:
        print(f"❌ LLM utility imports failed: {e}")
        return False
    
    return True

def test_connector_imports():
    """Test connector-related imports."""
    try:
        from con_mon_v2.connectors.models import ConnectorType
        print("✅ Connector imports successful")
    except Exception as e:
        print(f"❌ Connector imports failed: {e}")
        return False
    
    return True

def test_database_imports():
    """Test database utility imports."""
    try:
        from con_mon_v2.utils.db import get_db
        print("✅ Database utility imports successful")
    except Exception as e:
        print(f"❌ Database utility imports failed: {e}")
        return False
    
    return True

def test_service_imports():
    """Test service imports."""
    try:
        from con_mon_v2.utils.services import ResourceCollectionService
        print("✅ Service imports successful")
    except Exception as e:
        print(f"❌ Service imports failed: {e}")
        return False
    
    return True

def main():
    """Run all import tests."""
    print("🧪 Testing con_mon_v2 imports...")
    print("=" * 50)
    
    tests = [
        test_basic_imports,
        test_resource_imports,
        test_compliance_imports,
        test_llm_imports,
        test_connector_imports,
        test_database_imports,
        test_service_imports
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("=" * 50)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All import tests passed!")
        return 0
    else:
        print("❌ Some import tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
