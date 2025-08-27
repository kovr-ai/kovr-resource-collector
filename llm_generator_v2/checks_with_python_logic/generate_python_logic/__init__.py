"""
Dynamic model generation for services.
Models are automatically created from execution.yaml configuration.
"""

from pathlib import Path
from llm_generator_v2.yaml_loader import ExecutionYamlMapping
current_path = Path(__file__).parent
service_name = current_path.name
module_name = current_path.parent.name

# Get the execution.yaml path relative to this module
execution_yaml_path = Path(__file__).parents[2] / "execution.yaml"

# Load execution configuration
execution_config = ExecutionYamlMapping.load_yaml(execution_yaml_path)

# Find this service's configuration dynamically
service_config = None
module_config = None
for module in execution_config.modules:
    if module.name == module_name:
        module_config = module
        for step in module.steps:
            if step.name == service_name:
                service_config = step
                break
        break

if service_config is None:
    raise RuntimeError(f"Could not find service configuration for {module_name}.{service_name} in execution.yaml")

if module_config is None:
    raise RuntimeError(f"Could not find module configuration for {module_name} in execution.yaml")

# Create service instance with proper arguments
from .services import Service
service = Service(
    module_config=module_config,
    service_config=service_config
)

# Make dynamic Input and Output models available
Input = service.Input
Output = service.Output

# Dynamically extract all nested models from Input and Output
nested_models = {}
export_list = ['Input', 'Output', 'service']

# Extract nested models from Input
for field_name, field_info in Input.model_fields.items():
    nested_model = field_info.annotation

    if hasattr(nested_model, '__name__') and hasattr(nested_model, 'model_fields'):  # It's a proper Pydantic model
        input_model_name = f"Input{field_name.title()}"
        nested_models[input_model_name] = nested_model
        export_list.append(input_model_name)

# Extract nested models from Output
for field_name, field_info in Output.model_fields.items():
    nested_model = field_info.annotation

    if hasattr(nested_model, '__name__') and hasattr(nested_model, 'model_fields'):  # It's a proper Pydantic model
        output_model_name = f"Output{field_name.title()}"
        nested_models[output_model_name] = nested_model
        export_list.append(output_model_name)

# Make all nested models available in module namespace
for model_name, model_class in nested_models.items():
    globals()[model_name] = model_class

# Make all models and service available for import
__all__ = export_list
