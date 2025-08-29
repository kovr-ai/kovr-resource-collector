import os
import importlib

class Provider:
    def __init__(self, provider: str, metadata: dict):
        self.provider = provider
        self.metadata = metadata
        self.client = self.connect()
        self.services = self.load_services()

    def connect(self):
        print("connect: Not implemented for provider: ", self.provider)
        exit(1)

    def load_services(self):
        services_dir = os.path.join(os.path.dirname(__file__), f'{self.provider}/services')
        service_instances = []
        
        for filename in os.listdir(services_dir):
            if filename.endswith('.py') and filename != '__init__.py':
                service_name = filename[:-3]
                
                try:
                    module_name = f"providers.{self.provider}.services.{service_name}"
                    module = importlib.import_module(module_name)

                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (isinstance(attr, type) and 
                            hasattr(attr, '_is_service') and 
                            attr._is_service):
                            service_class = attr
                            service_instances.append({
                                "name": service_name,
                                "class": service_class
                            })
                    
                except Exception as e:
                    print(f"Error loading service {service_name}: {e}")

        return service_instances

    def process(self):
        pass

def provider_class(cls):
    cls._is_provider = True
    return cls