# Framework Extension Guide

This guide explains how to add new compliance frameworks to the system using the base framework architecture.

## Overview

The system now uses a modular, extensible architecture with:
- **BaseFramework**: Abstract base class for all compliance frameworks
- **BaseControlFamily**: Abstract base class for control families within frameworks
- **BaseControl**: Base class for individual controls
- **FrameworkRegistry**: Central registry for managing all frameworks

## Current Frameworks

- **NIST 800-53**: 30 controls across 8 families (AC, IA, SC, AU, CM, SI, IR, RA)
- **ISO 27001**: 4 controls across 2 families (A.5, A.6) - Example implementation

## Adding a New Framework

### Step 1: Create Framework Directory Structure

```
rules/frameworks/
├── your_framework/
│   ├── __init__.py
│   ├── your_framework.py
│   └── control_families/
│       ├── __init__.py
│       ├── family_1.py
│       ├── family_2.py
│       └── ...
```

### Step 2: Create Control Families

Each control family should inherit from `BaseControlFamily`:

```python
# rules/frameworks/your_framework/control_families/family_1.py
from rules.frameworks.base_control_family import BaseControlFamily
from rules.frameworks.base_control import BaseControl
from rules.checks.your_domain.your_check import YourCheck

class Family1(BaseControlFamily):
    """Your Framework Family 1"""
    
    def __init__(self):
        super().__init__(
            family_id="FAM1",
            family_name="Family 1 Name"
        )
        self.initialize_controls()
    
    def initialize_controls(self):
        """Initialize all controls in this family"""
        controls = [
            BaseControl(
                control_id="FAM1-01",
                control_name="Control 1 Name",
                checks=[YourCheck()]
            ),
            BaseControl(
                control_id="FAM1-02",
                control_name="Control 2 Name",
                checks=[YourCheck(), AnotherCheck()]
            ),
        ]
        
        for control in controls:
            self.add_control(control)
```

### Step 3: Create Framework Class

Your framework should inherit from `BaseFramework`:

```python
# rules/frameworks/your_framework/your_framework.py
from rules.frameworks.base_framework import BaseFramework
from .control_families.family_1 import Family1
from .control_families.family_2 import Family2

class YourFramework(BaseFramework):
    """Your Framework Implementation"""
    
    def __init__(self):
        super().__init__(
            framework_id="your_framework",
            framework_name="Your Framework Name"
        )
        self.initialize_families()
    
    def initialize_families(self):
        """Initialize all control families"""
        self.control_families = [
            Family1(),
            Family2(),
        ]
```

### Step 4: Register Framework

Add your framework to the registry:

```python
# rules/frameworks/framework_registry.py
from .your_framework.your_framework import YourFramework

class FrameworkRegistry:
    def _initialize_default_frameworks(self):
        # ... existing frameworks ...
        self.register_framework("your_framework", YourFramework())
```

### Step 5: Create Checks (if needed)

If you need new checks, create them in the appropriate domain:

```python
# rules/checks/your_domain/your_check.py
class YourCheck:
    def check_aws(self, data):
        # TODO: Implement AWS-specific logic
        return {
            "status": "NOT_IMPLEMENTED",
            "details": "AWS check not implemented"
        }
    
    def check_google_workspace(self, data):
        # TODO: Implement Google Workspace-specific logic
        return {
            "status": "NOT_IMPLEMENTED",
            "details": "Google Workspace check not implemented"
        }
```

## Using the Framework Registry

### Get Available Frameworks

```python
from rules.frameworks.framework_registry import framework_registry

# List all frameworks
frameworks = framework_registry.list_available_frameworks()
for fw in frameworks:
    print(f"{fw['framework_id']}: {fw['framework_name']}")

# Get specific framework
nist = framework_registry.get_framework("nist_800_53")
iso = framework_registry.get_framework("iso_27001")
```

### Get Framework Information

```python
# Get detailed info about a framework
info = framework_registry.get_framework_info("nist_800_53")
print(f"Total controls: {info['total_controls']}")
print(f"Total families: {info['total_families']}")

# Validate all frameworks
validation = framework_registry.validate_all_frameworks()
```

### Get Controls and Families

```python
# Get specific control
ac_02 = framework_registry.get_control_by_id("nist_800_53", "AC-02")

# Get specific family
ac_family = framework_registry.get_family_by_id("nist_800_53", "AC")
```

## Using the Rule Engine

### Single Framework

```python
from rule_engine import RuleEngine

# Use default framework (NIST 800-53)
rule_engine = RuleEngine("aws", data)
report = rule_engine.process()

# Use specific framework
rule_engine = RuleEngine("aws", data, framework_id="iso_27001")
report = rule_engine.process()
```

### Multiple Frameworks

```python
from rules.frameworks.framework_registry import framework_registry

# Process all frameworks
reports = {}
for framework_id in framework_registry.get_framework_ids():
    rule_engine = RuleEngine("aws", data, framework_id=framework_id)
    reports[framework_id] = rule_engine.process()
```

## Best Practices

### 1. Control ID Naming

Use consistent naming conventions:
- **NIST 800-53**: `AC-02`, `SC-28`, etc.
- **ISO 27001**: `A.5.1.1`, `A.6.1.2`, etc.
- **Your Framework**: `FAM1-01`, `FAM2-03`, etc.

### 2. Check Reusability

Design checks to be reusable across frameworks:
```python
# This check can be used in multiple frameworks
class MFAEnabledCheck:
    def check_aws(self, data):
        # AWS-specific MFA logic
        pass
    
    def check_google_workspace(self, data):
        # Google Workspace-specific MFA logic
        pass
```

### 3. Family Organization

Group related controls logically:
- **Access Control**: Authentication, authorization, session management
- **Data Protection**: Encryption, backup, retention
- **Monitoring**: Logging, auditing, alerting

### 4. Validation

Always validate your framework:
```python
# Check for duplicate control IDs
validation = framework_registry.get_framework_info("your_framework")
if not validation['validation']['valid']:
    print(f"Duplicate controls: {validation['validation']['duplicate_control_ids']}")
```

## Example: Adding SOC 2 Framework

Here's a complete example of adding a SOC 2 framework:

### 1. Create SOC 2 Families

```python
# rules/frameworks/soc_2/control_families/cc_family.py
from rules.frameworks.base_control_family import BaseControlFamily
from rules.frameworks.base_control import BaseControl
from rules.checks.access_control.user_account_management import UserAccountManagementCheck

class CCFamily(BaseControlFamily):
    """SOC 2 CC - Control Environment"""
    
    def __init__(self):
        super().__init__(
            family_id="CC",
            family_name="Control Environment"
        )
        self.initialize_controls()
    
    def initialize_controls(self):
        controls = [
            BaseControl(
                control_id="CC1.1",
                control_name="Commitment to Integrity and Ethical Values",
                checks=[UserAccountManagementCheck()]
            ),
        ]
        
        for control in controls:
            self.add_control(control)
```

### 2. Create SOC 2 Framework

```python
# rules/frameworks/soc_2/soc2_framework.py
from rules.frameworks.base_framework import BaseFramework
from .control_families.cc_family import CCFamily

class SOC2Framework(BaseFramework):
    def __init__(self):
        super().__init__(
            framework_id="soc_2",
            framework_name="SOC 2 Trust Services Criteria"
        )
        self.initialize_families()
    
    def initialize_families(self):
        self.control_families = [
            CCFamily(),
        ]
```

### 3. Register SOC 2

```python
# In framework_registry.py
from .soc_2.soc2_framework import SOC2Framework

def _initialize_default_frameworks(self):
    # ... existing frameworks ...
    self.register_framework("soc_2", SOC2Framework())
```

## Testing Your Framework

```python
# Test framework loading
from rules.frameworks.framework_registry import framework_registry

# Check if framework loads
your_fw = framework_registry.get_framework("your_framework")
print(f"Framework loaded: {your_fw.framework_name}")

# Test validation
info = framework_registry.get_framework_info("your_framework")
print(f"Validation passed: {info['validation']['valid']}")

# Test rule engine
from rule_engine import RuleEngine
rule_engine = RuleEngine("aws", {}, framework_id="your_framework")
report = rule_engine.process()
print(f"Report generated: {report['framework_name']}")
```

## Benefits of This Architecture

1. **Modularity**: Each framework is self-contained
2. **Reusability**: Checks can be shared across frameworks
3. **Extensibility**: Easy to add new frameworks
4. **Consistency**: Common interface across all frameworks
5. **Validation**: Built-in validation for control uniqueness
6. **Flexibility**: Support for different control naming schemes
7. **Maintainability**: Clear separation of concerns

This architecture makes it easy to add new compliance frameworks while maintaining consistency and reusability across the entire system. 