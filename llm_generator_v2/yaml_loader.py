import os
import yaml
from enum import Enum
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Type, Union
from pathlib import Path


class YamlFieldType(str, Enum):
    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    OBJECT = "object"
    LIST = "list"
    ANY = "any"

    @classmethod
    def yaml_field_type_to_python_type(cls, field_type: 'YamlFieldType') -> Type:
        type_mapping = {
            cls.STRING: str,
            cls.INTEGER: int,
            cls.BOOLEAN: bool,
            cls.OBJECT: dict,
            cls.LIST: list,
            cls.ANY: Any
        }
        return type_mapping.get(field_type, Any)


class YamlField(BaseModel):
    name: str
    dtype: YamlFieldType


class YamlModelMapping(BaseModel):
    pydantic_model: Type[BaseModel]  # Any Pydantic model is valid
    fields: List[YamlField]
    is_list: bool = False

    @classmethod
    def create_yaml_model(
            cls,
            name: str,
            annotations: dict,
            fields: dict,
            base_class: Type[BaseModel] = BaseModel
    ) -> Type[BaseModel]:
        """Create a new Pydantic model type with the given fields."""
        # Create the model class with only YAML-defined fields
        model = type(
            name,
            (base_class,),
            {
                '__annotations__': annotations,
                **fields
            }
        )
        return model

    @classmethod
    def process_yaml_dict(
            cls,
            yaml_data: dict[str, Any],
            parent_name: str = ""
    ) -> tuple[List[YamlField], dict, dict]:
        fields = []
        model_annotations = {}
        model_fields = {}

        for field_name, field_def in yaml_data.items():
            is_field_list = field_name.endswith('[]')
            clean_field_name = field_name[:-2] if is_field_list else field_name

            if isinstance(field_def, str):
                # Get the base type (string, integer, etc.)
                field_type = YamlFieldType(field_def) if field_def in YamlFieldType._value2member_map_ else YamlFieldType.ANY
                python_type = YamlFieldType.yaml_field_type_to_python_type(field_type)
                
                if is_field_list:
                    # For array types, wrap the base type in List
                    yaml_field = YamlField(name=clean_field_name, dtype=YamlFieldType.LIST)
                    model_annotations[clean_field_name] = List[python_type]
                    model_fields[clean_field_name] = Field(default_factory=list)
                else:
                    # For non-array types
                    yaml_field = YamlField(name=clean_field_name, dtype=field_type)
                    model_annotations[clean_field_name] = python_type
                    model_fields[clean_field_name] = Field(default=None)
                
                fields.append(yaml_field)

            elif isinstance(field_def, dict):
                nested_name = f"{parent_name}_{clean_field_name}" if parent_name else clean_field_name
                nested_fields, nested_annotations, nested_field_defs = cls.process_yaml_dict(field_def, nested_name)

                nested_model = cls.create_yaml_model(
                    name=nested_name.title(),
                    annotations=nested_annotations,
                    fields=nested_field_defs
                )

                if is_field_list:
                    yaml_field = YamlField(name=clean_field_name, dtype=YamlFieldType.LIST)
                    model_annotations[clean_field_name] = List[nested_model]
                    model_fields[clean_field_name] = Field(default_factory=list)
                else:
                    yaml_field = YamlField(name=clean_field_name, dtype=YamlFieldType.OBJECT)
                    model_annotations[clean_field_name] = nested_model
                    model_fields[clean_field_name] = Field(default=None)

                fields.append(yaml_field)
                fields.extend(nested_fields)

        return fields, model_annotations, model_fields

    @classmethod
    def load_yaml(
            cls,
            yaml_dict: dict[str, Any],
    ) -> 'YamlModelMapping':
        model_name = next(iter(yaml_dict))
        fields, model_annotations, model_fields = cls.process_yaml_dict(yaml_dict[model_name])
        is_list = any(field_name.endswith('[]') for field_name in yaml_dict[model_name].keys())
        model_type = cls.create_yaml_model(
            name=model_name,
            annotations=model_annotations,
            fields=model_fields
        )
        return cls(
            pydantic_model=model_type,
            fields=fields,
            is_list=is_list
        )


class ServiceYamlField(BaseModel):
    index: int
    name: str
    input_model: YamlModelMapping
    output_model: YamlModelMapping


class ModuleYamlMapping(BaseModel):
    index: int
    name: str
    steps: List[ServiceYamlField]


class ExecutionYamlMapping(BaseModel):
    """Mapping class for schema configurations from YAML (e.g., schemas.yaml)."""
    modules: List[ModuleYamlMapping]
    
    @staticmethod
    def _load_yaml_data(path_or_dict: str | Path | dict) -> dict:
        """Load YAML data from file path or dict."""
        if isinstance(path_or_dict, (str, Path)):
            if not os.path.exists(str(path_or_dict)):
                raise FileNotFoundError(f"YAML file not found: {path_or_dict}")
            
            with open(path_or_dict, 'r') as file:
                return yaml.safe_load(file)
        elif isinstance(path_or_dict, dict):
            return path_or_dict
        else:
            raise ValueError("Input must be either a file path (str or Path) or a dictionary")

    @classmethod
    def _resolve_references(
        cls,
        model_def: Dict[str, Any], 
        step_namespace: str, 
        all_schemas: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Resolve schema references like 'benchmark_and_checks_literature.generate_benchmark_literature.Input'.
        
        Args:
            model_def: The model definition to resolve references in
            step_namespace: The schema namespace (e.g., 'benchmark_and_checks_literature')
            all_schemas: All schema definitions
            
        Returns:
            Dict with references resolved to actual schema definitions
        """
        resolved = {}
        
        for field_name, field_def in model_def.items():
            if isinstance(field_def, list):
                # Handle array fields like checks[]: ["benchmark_and_checks_literature.Check"]
                resolved_items = []
                for item in field_def:
                    if isinstance(item, str) and '.' in item:
                        # This is a reference like "benchmark_and_checks_literature.Check"
                        namespace, ref_name = item.split('.', 1)
                        if namespace in all_schemas and ref_name in all_schemas[namespace]:
                            resolved_items.append(all_schemas[namespace][ref_name])
                        else:
                            resolved_items.append(item)  # Keep as-is if not found
                    else:
                        resolved_items.append(item)
                resolved[field_name] = resolved_items
            elif isinstance(field_def, dict):
                # Recursively resolve references in nested objects
                resolved[field_name] = cls._resolve_references(field_def, step_namespace, all_schemas)
            else:
                # Keep field as-is
                resolved[field_name] = field_def
        
        return resolved
    
    @classmethod
    def load_yaml(
            cls,
            path_or_dict: str | Path | dict
    ) -> 'ExecutionYamlMapping':
        """
        Load execution configuration from a YAML file or dictionary.
        
        Args:
            path_or_dict: Either a path to a YAML file or a dictionary containing the YAML data
            
        Returns:
            ExecutionYamlMapping: The complete execution mapping with all modules and steps
        """
        yaml_data = cls._load_yaml_data(path_or_dict)
        
        if not yaml_data or not isinstance(yaml_data, dict):
            raise ValueError("Invalid YAML data: expected a dictionary with execution configuration")
        
        modules = []
        
        # Process each top-level module (e.g., benchmark_and_checks_literature)
        for module_index, (module_name, module_steps) in enumerate(yaml_data.items()):
            if not isinstance(module_steps, dict):
                continue
                
            steps = []
            
            # Process each step within the module (e.g., generate_benchmark_literature)
            for step_index, (step_name, step_def) in enumerate(module_steps.items()):
                if isinstance(step_def, dict):
                    # Extract input and output definitions
                    input_def = step_def.get('input', {})
                    output_def = step_def.get('output', {})
                    
                    # Resolve any references within input/output models
                    resolved_input = cls._resolve_references(input_def, module_name, yaml_data) if input_def else {}
                    resolved_output = cls._resolve_references(output_def, module_name, yaml_data) if output_def else {}
                    
                    # Create model mappings for input and output
                    input_mapping = YamlModelMapping.load_yaml({'input': resolved_input}) if resolved_input else None
                    output_mapping = YamlModelMapping.load_yaml({'output': resolved_output}) if resolved_output else None
                    
                    if input_mapping and output_mapping:
                        service_field = ServiceYamlField(
                            index=step_index,
                            name=step_name,
                            input_model=input_mapping,
                            output_model=output_mapping
                        )
                        steps.append(service_field)
            
            if steps:
                module_mapping = ModuleYamlMapping(
                    index=module_index,
                    name=module_name,
                    steps=steps
                )
                modules.append(module_mapping)
        
        return cls(modules=modules)
