"""
Checks module for resource validation and evaluation.
"""
import yaml
import os
from typing import Dict, Any

# Global storage for loaded checks
_loaded_checks: Dict[str, Dict[str, Any]] = {}

def load_checks_from_yaml(yaml_file_path: str = None):
    """
    Load checks from YAML file and make them accessible as module attributes.
    
    Args:
        yaml_file_path: Path to YAML file, defaults to checks/checks.yaml
    """
    global _loaded_checks
    
    if yaml_file_path is None:
        # Default to checks.yaml in the same directory as this file
        current_dir = os.path.dirname(__file__)
        yaml_file_path = os.path.join(current_dir, 'checks.yaml')
    
    try:
        with open(yaml_file_path, 'r') as file:
            yaml_data = yaml.safe_load(file)
        
        # Process github_checks
        if 'github_checks' in yaml_data:
            for check_config in yaml_data['github_checks']:
                check_name = check_config['name']
                _loaded_checks[check_name] = check_config
                
                # Make accessible as module attribute
                globals()[check_name] = check_config
        
        print(f"✅ Loaded {len(_loaded_checks)} checks from {yaml_file_path}")
        
    except FileNotFoundError:
        print(f"❌ Checks YAML file not found: {yaml_file_path}")
    except Exception as e:
        print(f"❌ Error loading checks from YAML: {e}")

def get_loaded_checks() -> Dict[str, Dict[str, Any]]:
    """Get all loaded checks."""
    return _loaded_checks.copy()

# Auto-load checks when module is imported
load_checks_from_yaml() 
