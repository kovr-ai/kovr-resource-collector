from providers.provider import Provider, provider_class
from constants import Providers
from google.oauth2 import service_account
from googleapiclient.discovery import build


SERVICE_ACCOUNT_FILE = "google_credentials.json"
IMPERSONATED_ADMIN_EMAIL = "vibhor@kovr.ai"
SCOPES = ['https://www.googleapis.com/auth/admin.directory.user.readonly']

@provider_class
class GoogleProvider(Provider):
    def __init__(self, data: dict):
        super().__init__(Providers.GOOGLE.value, data)

        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            scopes=SCOPES,
            subject=IMPERSONATED_ADMIN_EMAIL  # This is the key part: impersonation
        )

        service = build('admin', 'directory_v1', credentials=credentials)
        self.client = service

    def process(self):
        results = self.client.users().list(customer='my_customer', maxResults=10, orderBy='email').execute()
        users = results.get('users', [])
        return {
            "users": users
        }
