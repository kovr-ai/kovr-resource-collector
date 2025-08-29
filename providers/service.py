class BaseService:
    def __init__(self, client):
        self.client = client

    def process(self):
        pass

def service_class(cls):
    cls._is_service = True
    return cls