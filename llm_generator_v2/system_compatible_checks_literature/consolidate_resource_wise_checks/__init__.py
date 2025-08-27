# Step 2: Consolidate Resource-wise Checks (NON-LLM)
"""
This step consolidates multiple checks that apply to the same resource,
separating valid and invalid resources and organizing the literature and field paths.
"""

from llm_generator_v2.yaml_loader import ExecutionYamlMapping

# Load execution configuration
execution_config = ExecutionYamlMapping.load_yaml("llm_generator_v2/execution.yaml")
module_config = None
for module in execution_config.modules:
    if module.name == "system_compatible_checks_literature":
        module_config = module
        break

if module_config is None:
    raise RuntimeError("Could not find module configuration for system_compatible_checks_literature")

service_config = None
for step in module_config.steps:
    if step.name == "consolidate_resource_wise_checks":
        service_config = step
        break

if service_config is None:
    raise RuntimeError("Could not find service configuration for consolidate_resource_wise_checks")

# Generate dynamic models
Input = service_config.input_model.pydantic_model
InputCheck = getattr(Input.model_fields['check'].annotation, '__args__', [Input.model_fields['check'].annotation])[0]
InputResource = getattr(InputCheck.model_fields['resource'].annotation, '__args__', [InputCheck.model_fields['resource'].annotation])[0]

Output = service_config.output_model.pydantic_model
OutputCheck = getattr(Output.model_fields['check'].annotation, '__args__', [Output.model_fields['check'].annotation])[0]

# Create service instance
from llm_generator_v2.system_compatible_checks_literature.consolidate_resource_wise_checks.services import ConsolidateResourceWiseChecksService
service = ConsolidateResourceWiseChecksService(module_config, service_config)
