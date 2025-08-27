# Step 1: Add Targeted Literature per check Resource wise and Field Paths
"""
This step uses an LLM to analyze security checks and generate targeted literature
for specific cloud resources and their field paths, determining if the resource
is valid for the check and providing detailed remediation guidance.
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
    if step.name == "add_targeted_literature":
        service_config = step
        break

if service_config is None:
    raise RuntimeError("Could not find service configuration for add_targeted_literature")

# Generate dynamic models
Input = service_config.input_model.pydantic_model
InputCheck = getattr(Input.model_fields['check'].annotation, '__args__', [Input.model_fields['check'].annotation])[0]
InputResource = getattr(InputCheck.model_fields['resource'].annotation, '__args__', [InputCheck.model_fields['resource'].annotation])[0]

Output = service_config.output_model.pydantic_model  
OutputResource = getattr(Output.model_fields['resource'].annotation, '__args__', [Output.model_fields['resource'].annotation])[0]
OutputStatements = getattr(OutputResource.model_fields['output_statements'].annotation, '__args__', [OutputResource.model_fields['output_statements'].annotation])[0]
OutputFixDetails = getattr(OutputResource.model_fields['fix_details'].annotation, '__args__', [OutputResource.model_fields['fix_details'].annotation])[0]

# Create service instance
from llm_generator_v2.system_compatible_checks_literature.add_targeted_literature.services import AddTargetedLiteratureService
service = AddTargetedLiteratureService(module_config, service_config)
