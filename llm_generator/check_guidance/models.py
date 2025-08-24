from pathlib import Path
from typing import List, Dict, Type
from pydantic import BaseModel
from con_mon.utils.yaml_loader import SchemaYamlMapping

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

    schema_mappings = SchemaYamlMapping.load_yaml(schema_path)

    models = {}

    # Extract models from the schema mapping
    for schema_name, mapping in schema_mappings.items():
        # Add all models from this schema namespace
        for model_name, model_mapping in mapping.models.items():
            models[model_name] = model_mapping.pydantic_model

    return models


_models_and_names: Dict[str, Type[BaseModel]] = generate_models_from_schema_yaml()
MODEL_NAMES: List[str] = list(_models_and_names.keys())
for _model_name, _model_class in _models_and_names.items():
    globals()[_model_name] = _model_class
