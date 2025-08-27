"""
Checks with Python Logic Module

Implements Section 3: Generating Python Logic from enriched checks.
"""

from llm_generator_v2.yaml_loader import ExecutionYamlMapping
from pathlib import Path

# Load execution configuration
execution_config = ExecutionYamlMapping.load_yaml(
    Path(__file__).parent.parent / "execution.yaml"
)

# Find this module's configuration
module_config = None
for module in execution_config.modules:
    if module.name == "checks_with_python_logic":
        module_config = module
        break

if not module_config:
    raise RuntimeError("Could not find module configuration for checks_with_python_logic in execution.yaml")

# Expose module configuration
__all__ = ['module_config', 'execution_config']
