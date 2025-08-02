"""
Checks module for resource validation and evaluation.
"""
import yaml
import os
from typing import Dict, Any, Callable
from .models import Check, ComparisonOperation, ComparisonOperationEnum

# Global storage for loaded checks
_loaded_checks: Dict[str, Check] = {}
_custom_functions: Dict[str, Callable] = {}

def load_checks_from_yaml(yaml_file_path: str = None):
    """
    Load checks from YAML file and make them accessible as module attributes.
    
    Args:
        yaml_file_path: Path to YAML file, defaults to checks/checks.yaml
    """
    global _loaded_checks, _custom_functions
    
    if yaml_file_path is None:
        # Default to checks.yaml in the same directory as this file
        current_dir = os.path.dirname(__file__)
        yaml_file_path = os.path.join(current_dir, 'checks.yaml')
    
    try:
        with open(yaml_file_path, 'r') as file:
            config = yaml.safe_load(file)
        
        # Load custom functions first
        if 'custom_functions' in config:
            _load_custom_functions(config['custom_functions'])
        
        # Load checks
        if 'checks' in config:
            for check_config in config['checks']:
                check = _create_check_from_config(check_config)
                _loaded_checks[check.name] = check
                
                # Make check accessible as module attribute
                globals()[check.name] = check
        
        print(f"✅ Loaded {len(_loaded_checks)} checks from {yaml_file_path}")
        
    except FileNotFoundError:
        print(f"❌ YAML file not found: {yaml_file_path}")
    except yaml.YAMLError as e:
        print(f"❌ Error parsing YAML: {e}")
    except Exception as e:
        print(f"❌ Error loading checks: {e}")

def _load_custom_functions(functions_config: Dict[str, Any]):
    """Load custom functions from YAML configuration."""
    global _custom_functions
    
    for func_name, func_config in functions_config.items():
        if 'implementation' in func_config:
            try:
                # Execute the function code to create the function
                exec_globals = {}
                exec(func_config['implementation'], exec_globals)
                
                # Find the function in the executed globals
                for name, obj in exec_globals.items():
                    if callable(obj) and not name.startswith('_'):
                        _custom_functions[func_name] = obj
                        break
                        
            except Exception as e:
                print(f"❌ Error loading custom function {func_name}: {e}")

def _create_check_from_config(check_config: Dict[str, Any]) -> Check:
    """Create a Check object from YAML configuration."""
    
    # Parse operation
    operation_config = check_config['operation']
    operation_name = operation_config['name']
    
    # Create ComparisonOperation
    if operation_name == "custom":
        custom_func_name = operation_config.get('custom_function_name')
        custom_function = _custom_functions.get(custom_func_name)
        
        if not custom_function:
            raise ValueError(f"Custom function '{custom_func_name}' not found")
            
        operation = ComparisonOperation(
            name=ComparisonOperationEnum.CUSTOM,
            custom_function=custom_function
        )
    else:
        # Map string to enum
        operation_enum = ComparisonOperationEnum(operation_name)
        operation = ComparisonOperation(name=operation_enum)
    
    # Create Check object
    return Check(
        name=check_config['name'],
        field_path=check_config['field_path'],
        operation=operation,
        expected_value=check_config['expected_value'],
        description=check_config.get('description')
    )

def get_loaded_checks() -> Dict[str, Check]:
    """Get all loaded checks."""
    return _loaded_checks.copy()

def get_check(name: str) -> Check:
    """Get a specific check by name."""
    return _loaded_checks.get(name)

# Auto-load checks when module is imported
load_checks_from_yaml() 
