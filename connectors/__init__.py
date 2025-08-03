"""
Connectors module for data fetching service definitions.

Auto-generated imports available:
- ConnectorService objects: github, aws, etc. (based on YAML config)
- Input models: GithubInput, AwsInput, etc. (short names)
- Output models: GithubOutput, AwsOutput, etc. (short names)
- Full model names: GithubConnectorInput, GithubConnectorOutput, etc.

Usage:
    from connectors import github, GithubInput, GithubOutput
    
    input_config = GithubInput(token='...', org_name='...')
    result = github.fetch_data(input_config)
"""
import yaml
import os
import importlib
from typing import Dict, Any, List, Type
from pydantic import BaseModel, create_model
from .models import ConnectorService, ConnectorType, ConnectorInput, ConnectorOutput

# Global storage for loaded connectors
_loaded_connectors: Dict[str, Dict[str, Any]] = {}
_connector_services: Dict[str, List[ConnectorService]] = {}
_connector_models: Dict[str, Dict[str, Type[BaseModel]]] = {}

# This will be populated dynamically during loading
__all__ = [
    'ConnectorService', 'ConnectorType', 'ConnectorInput', 'ConnectorOutput',
    'get_loaded_connectors', 'get_connector_services', 'get_all_connector_services', 'get_connector_models'
]

def _create_dynamic_model(name: str, fields_spec: Dict[str, str], base_class: Type[BaseModel]) -> Type[BaseModel]:
    """Create a dynamic Pydantic model from YAML field specifications."""
    field_definitions = {}
    
    for field_name, field_type in fields_spec.items():
        if field_type == "string":
            field_definitions[field_name] = (str, None)
        elif field_type == "integer":
            field_definitions[field_name] = (int, None)
        elif field_type == "boolean":
            field_definitions[field_name] = (bool, None)
        elif field_type == "array":
            field_definitions[field_name] = (list, None)
        elif field_type == "object":
            field_definitions[field_name] = (dict, None)
        else:
            field_definitions[field_name] = (Any, None)
    
    return create_model(name, **field_definitions, __base__=base_class)

def _create_provider_wrapper(provider_class, method_name, connector_config):
    """Create a wrapper function for provider class methods."""
    def fetch_function(*args, **kwargs):
        # Extract metadata from kwargs or create default
        metadata = kwargs.get('metadata', {})
        if not metadata and connector_config.get('auth'):
            # Create metadata from connector config
            import os
            token_env_var = connector_config['auth'].get('token_env_var', 'GITHUB_TOKEN')
            token = os.getenv(token_env_var)
            if token:
                metadata = {token_env_var: token}
        
        # Instantiate provider
        provider_instance = provider_class(metadata)
        
        # Connect if method exists
        if hasattr(provider_instance, 'connect'):
            provider_instance.connect()
        
        # Call the method
        method = getattr(provider_instance, method_name)
        return method(*args, **kwargs)
    return fetch_function

def _create_connector_service(service_config: Dict[str, Any], connector_config: Dict[str, Any]) -> ConnectorService:
    """Create a ConnectorService object from service configuration."""
    try:
        # Dynamic import of the provider service module
        provider_service_path = service_config['provider_service']
        method_name = service_config['method']
        
        # Import the module
        module = importlib.import_module(provider_service_path)
        
        # Check if this is a class method (for providers) or module function
        if hasattr(module, method_name):
            # Direct module function
            fetch_function = getattr(module, method_name)
        else:
            # Look for provider class and create wrapper
            provider_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    hasattr(attr, '_is_provider') and 
                    attr._is_provider):
                    provider_class = attr
                    break
            
            if provider_class and hasattr(provider_class, method_name):
                # Create wrapper function for class method
                fetch_function = _create_provider_wrapper(provider_class, method_name, connector_config)
            else:
                raise AttributeError(f"Method '{method_name}' not found in module or provider class")
        
        # Create ConnectorService
        connector_type = ConnectorType(connector_config['connector_type'])
        
        return ConnectorService(
            name=service_config['name'],
            connector_type=connector_type,
            fetch_function=fetch_function
        )
        
    except Exception as e:
        print(f"❌ Error creating connector service {service_config['name']}: {e}")
        return None

def load_connectors_from_yaml(yaml_file_path: str = None):
    """
    Load connector configurations from YAML file and create ConnectorService objects.
    
    Args:
        yaml_file_path: Path to YAML file, defaults to connectors/connectors.yaml
    """
    global _loaded_connectors, _connector_services, _connector_models, __all__
    
    if yaml_file_path is None:
        # Default to connectors.yaml in the same directory as this file
        current_dir = os.path.dirname(__file__)
        yaml_file_path = os.path.join(current_dir, 'connectors.yaml')
    
    try:
        with open(yaml_file_path, 'r') as file:
            yaml_data = yaml.safe_load(file)
        
        # Process connectors
        if 'connectors' in yaml_data:
            for connector_name, connector_config in yaml_data['connectors'].items():
                _loaded_connectors[connector_name] = connector_config
                
                # Add connector name to __all__
                __all__.append(connector_name)
                
                # Create dynamic input/output models if specified
                models = {}
                if 'input' in connector_config:
                    input_model = _create_dynamic_model(
                        f"{connector_name.title()}ConnectorInput",
                        connector_config['input'],
                        ConnectorInput
                    )
                    models['input'] = input_model
                    
                    # Make input model available for direct import
                    # Both full name and short name
                    full_input_name = f"{connector_name.title()}ConnectorInput"
                    short_input_name = f"{connector_name.title()}Input"
                    globals()[full_input_name] = input_model
                    globals()[short_input_name] = input_model
                    
                    # Add to __all__ for discoverability
                    __all__.extend([full_input_name, short_input_name])
                
                if 'output' in connector_config:
                    output_model = _create_dynamic_model(
                        f"{connector_name.title()}ConnectorOutput", 
                        connector_config['output'],
                        ConnectorOutput
                    )
                    models['output'] = output_model
                    
                    # Make output model available for direct import
                    # Both full name and short name
                    full_output_name = f"{connector_name.title()}ConnectorOutput"
                    short_output_name = f"{connector_name.title()}Output"
                    globals()[full_output_name] = output_model
                    globals()[short_output_name] = output_model
                    
                    # Add to __all__ for discoverability
                    __all__.extend([full_output_name, short_output_name])
                
                _connector_models[connector_name] = models
                
                # Create ConnectorService objects for each service
                services = []
                for service_config in connector_config.get('services', []):
                    service = _create_connector_service(service_config, connector_config)
                    if service:
                        services.append(service)
                
                _connector_services[connector_name] = services
                
                # Make accessible as module attribute
                # If there's only one service, return it directly for easy access
                # If multiple services, create a wrapper with the primary service as default
                if len(services) == 1:
                    # Single service - return ConnectorService directly
                    connector_obj = services[0]
                    # Add metadata for backward compatibility
                    connector_obj._config = connector_config
                    connector_obj._models = models
                    connector_obj._services = services
                elif len(services) > 1:
                    # Multiple services - create a wrapper class
                    class ConnectorWrapper:
                        def __init__(self, services, config, models):
                            self._services = services
                            self._config = config
                            self._models = models
                            # Use first service as default
                            self._default_service = services[0]
                        
                        def fetch_data(self, input_config: ConnectorInput) -> ConnectorOutput:
                            """Fetch data using the default (first) service."""
                            return self._default_service.fetch_data(input_config)
                        
                        def get_service(self, service_name: str) -> ConnectorService:
                            """Get a specific service by name."""
                            for service in self._services:
                                if service.name == service_name:
                                    return service
                            raise ValueError(f"Service '{service_name}' not found")
                        
                        def list_services(self) -> List[str]:
                            """List all available service names."""
                            return [service.name for service in self._services]
                        
                        @property
                        def config(self):
                            return self._config
                        
                        @property
                        def models(self):
                            return self._models
                        
                        @property
                        def services(self):
                            return self._services
                    
                    connector_obj = ConnectorWrapper(services, connector_config, models)
                else:
                    # No services - return config dict for backward compatibility
                    connector_obj = {
                        'config': connector_config,
                        'services': services,
                        'models': models
                    }
                
                globals()[connector_name] = connector_obj
        
        total_services = sum(len(services) for services in _connector_services.values())
        print(f"✅ Loaded {len(_loaded_connectors)} connectors with {total_services} services from {yaml_file_path}")
        
    except FileNotFoundError:
        print(f"❌ Connectors YAML file not found: {yaml_file_path}")
    except Exception as e:
        print(f"❌ Error loading connectors from YAML: {e}")

def get_loaded_connectors() -> Dict[str, Dict[str, Any]]:
    """Get all loaded connector configurations."""
    return _loaded_connectors.copy()

def get_connector_services(connector_name: str) -> List[ConnectorService]:
    """Get ConnectorService objects for a specific connector."""
    return _connector_services.get(connector_name, [])

def get_all_connector_services() -> Dict[str, List[ConnectorService]]:
    """Get all ConnectorService objects grouped by connector."""
    return _connector_services.copy()

def get_connector_models(connector_name: str) -> Dict[str, Type[BaseModel]]:
    """Get input/output models for a specific connector."""
    return _connector_models.get(connector_name, {})

# Auto-load connectors when module is imported
load_connectors_from_yaml() 