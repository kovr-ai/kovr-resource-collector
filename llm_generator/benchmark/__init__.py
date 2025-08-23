"""
Benchmark Generator Package - Section 1 Implementation

This package implements the complete benchmark metadata generation process:
- Step 1: Extract Checks Literature
- Step 2: Map to Controls and Existing Benchmarks
- Step 3: Coverage Reporting

Only services and models (dynamically generated) are exported from here.
"""

# Import core services
from pathlib import Path
from typing import Dict, Type
from pydantic import BaseModel
from .services import (
    generate_metadata,
    generate_checks_metadata, 
    generate_coverage_report
)


def generate_models_from_schema_yaml() -> Dict[str, Type[BaseModel]]:
    """
    Generate Pydantic models from schemas.yaml file using SchemaYamlMapping.
    
    Returns:
        Dict[str, Type[BaseModel]]: Dictionary mapping model names to Pydantic model classes
    """
    # Get the path to schemas.yaml in the same directory as this file
    schema_path = Path(__file__).parent / "schemas.yaml"
    
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    # Use SchemaYamlMapping to load the schema-specific format
    from con_mon.utils.yaml_loader import SchemaYamlMapping
    schema_mappings = SchemaYamlMapping.load_yaml(schema_path)
    
    models = {}
    
    # Extract models from the schema mapping
    for schema_name, mapping in schema_mappings.items():
        # Add all models from this schema namespace
        for model_name, model_mapping in mapping.models.items():
            models[model_name] = model_mapping.pydantic_model
    
    return models


_models_and_names: Dict[str, Type[BaseModel]] = generate_models_from_schema_yaml()
for _model_name, _model_class in _models_and_names.items():
    globals()[_model_name] = _model_class

# Package exports
__all__ = [
    # Service Methods (Section 1 Steps)
    'generate_metadata',          # Step 1: Extract Checks Literature
    'generate_checks_metadata',   # Step 2: Map to Controls
    'generate_coverage_report',   # Step 3: Coverage Reporting
] + list(_models_and_names.keys())
