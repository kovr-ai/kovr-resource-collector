import json
import importlib

from constants import Providers

class Collector:
    def __init__(self, provider: Providers, metadata: str):
        self.provider = provider
        self.metadata = self.decrypt_data(metadata)
        self.provider_instance = self.load_provider()
    
    def decrypt_data(self, data):
        try:
            if isinstance(data, str):
                data = json.loads(data)

            if not isinstance(data, dict):
                raise ValueError("Invalid data type")
            
            return data
        except Exception as e:
            raise ValueError(f"Error decrypting data: {e}")

    def load_provider(self):
        try:
            module = importlib.import_module(f"providers.{self.provider}.{self.provider}_provider")
            
            provider_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    hasattr(attr, '_is_provider') and 
                    attr._is_provider):
                    provider_class = attr
                    break
            
            if provider_class is None:
                raise ValueError(f"No provider class found in {self.provider} module")
            
            return provider_class(self.metadata)
            
        except ImportError:
            raise ValueError(f"Provider '{self.provider}' not found")
        except Exception as e:
            raise ValueError(f"Error loading provider '{self.provider}': {e}")
        
    def process(self):
        if self.provider_instance:
            return self.provider_instance.process()
        return None