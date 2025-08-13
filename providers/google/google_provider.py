from providers.provider import Provider, provider_class
from constants import Providers
from google.oauth2 import service_account
from googleapiclient.discovery import build
import boto3
import json
from con_mon.resources import GoogleInfoData
from typing import Dict, List, Tuple

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

    def process(self) -> Tuple[GoogleInfoData, Dict[str, List]]:
        results = self.client.users().list(customer='my_customer', maxResults=10, orderBy='email').execute()
        users = results.get('users', [])
        
        # Create InfoData object
        info_data = GoogleInfoData(
            account_id=self.data.get('super_admin_email', 'unknown'),
            users=[
                {
                    'id': user.get('id', ''),
                    'name': user.get('name', {}).get('fullName', ''),
                    'email': user.get('primaryEmail', '')
                }
                for user in users
            ],
            groups=[]  # Could be populated with actual groups data
        )
        
        # For now, return the raw data as second element (this should be a proper ResourceCollection)
        resource_data = {
            "users": users
        }
        
        return info_data, resource_data