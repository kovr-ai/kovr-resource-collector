"""
Generate Python Logic Service

Generates field_path and Python logic from enriched checks using existing CheckPrompt patterns.
"""

from llm_generator_v2.yaml_loader import ExecutionYamlMapping
from pathlib import Path

# Load execution configuration
execution_config = ExecutionYamlMapping.load_yaml(
    Path(__file__).parent.parent.parent / "execution.yaml"
)

# Find this module's configuration
module_config = None
for module in execution_config.modules:
    if module.name == "checks_with_python_logic":
        module_config = module
        break

if not module_config:
    raise RuntimeError("Could not find module configuration for checks_with_python_logic in execution.yaml")

# Find this service's configuration
service_config = None
for step in module_config.steps:
    if step.name == "generate_python_logic":
        service_config = step
        break

if not service_config:
    raise RuntimeError("Could not find service configuration for generate_python_logic in execution.yaml")

# Expose the Pydantic models from the service configuration
Input = service_config.input_model.pydantic_model
Output = service_config.output_model.pydantic_model

# Extract nested models for convenience (following pattern from Section 1)
# For input[].check structure
InputCheck = Input.model_fields['check'].annotation

# For input[].check.resource structure
InputResource = InputCheck.model_fields['resource'].annotation

# For output[].resource structure  
OutputResource = Output.model_fields['resource'].annotation

# Expose models
__all__ = ['Input', 'InputCheck', 'InputResource', 'Output', 'OutputResource', 'service_config']
