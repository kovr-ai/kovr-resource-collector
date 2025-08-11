from providers.provider import Provider, provider_class
from constants import Providers
from google.oauth2 import service_account
from googleapiclient.discovery import build
import boto3
import json

SERVICE_ACCOUNT_SECRET = "Connector-GWS-credentials"
SCOPES = ['https://www.googleapis.com/auth/admin.directory.user.readonly']

@provider_class
class GoogleProvider(Provider):
    def __init__(self, data: dict):
        self.data = data
        super().__init__(Providers.GOOGLE.value, data)

    def connect(self):
        service_account_info = self.get_service_account_secret_from_aws()

        credentials = service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=SCOPES,
            subject=self.data.get('super_admin_email')
        )

        service = build('admin', 'directory_v1', credentials=credentials)
        self.client = service

    def get_service_account_secret_from_aws(self):
        boto3.setup_default_session(region_name='us-west-2')
        secrets_client = boto3.client('secretsmanager')
        response = secrets_client.get_secret_value(SecretId=SERVICE_ACCOUNT_SECRET)
        return json.loads(response['SecretString'])

    def process(self):
        results = self.client.users().list(customer='my_customer', maxResults=10, orderBy='email').execute()
        users = results.get('users', [])
        return {
            "users": users
        }