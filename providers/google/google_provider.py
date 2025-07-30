from providers.provider import Provider, provider_class
from constants import Providers
@provider_class
class GoogleProvider(Provider):
    def __init__(self, data: dict):
        super().__init__(Providers.GOOGLE.value, data)

    def process(self):
        return {
            "type": "google",
        }