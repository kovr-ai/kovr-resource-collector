from providers.provider import Provider, provider_class
from constants import Providers
from google.oauth2 import service_account
from googleapiclient.discovery import build
import boto3
import json
from con_mon.mappings.google import GoogleInfoData, UserResource, GroupResource, GoogleResourceCollection
from typing import Dict, List, Tuple
from con_mon.utils.config import settings
from datetime import datetime

SERVICE_ACCOUNT_SECRET = "Connector-GWS-credentials"
SCOPES = [
    'https://www.googleapis.com/auth/admin.directory.user.readonly',
    'https://www.googleapis.com/auth/admin.directory.group.readonly',
]

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
        # session = boto3.Session(profile_name=settings.AWS_PROFILE)
        # secrets_client = session.client('secretsmanager')
        secrets_client = boto3.client('secretsmanager')
        response = secrets_client.get_secret_value(SecretId=SERVICE_ACCOUNT_SECRET)
        return json.loads(response['SecretString'])

    def process(self) -> Tuple[GoogleInfoData, GoogleResourceCollection]:
        # Fetch all users
        results = self.client.users().list(customer='my_customer', maxResults=500, orderBy='email').execute()
        users = results.get('users', [])
        
        # Fetch all groups
        results = self.client.groups().list(customer='my_customer', maxResults=500, orderBy='email').execute()
        groups = results.get('groups', [])

        # Create GoogleUserResource objects
        user_resources = []
        for user in users:
            user_resource = UserResource(
                id=f"google-user-{user.get('id', '')}",
                source_connector='google',
                user_id=user.get('id', ''),
                user_data={
                    'basic_info': {
                        'kind': user.get('kind', ''),
                        'id': user.get('id', ''),
                        'etag': user.get('etag', ''),
                        'primaryEmail': user.get('primaryEmail', ''),
                        'customerId': user.get('customerId', ''),
                        'lastLoginTime': user.get('lastLoginTime', ''),
                        'creationTime': user.get('creationTime', ''),
                        'agreedToTerms': user.get('agreedToTerms', False),
                        'suspended': user.get('suspended', False),
                        'archived': user.get('archived', False),
                        'changePasswordAtNextLogin': user.get('changePasswordAtNextLogin', False),
                        'ipWhitelisted': user.get('ipWhitelisted', False),
                        'isMailboxSetup': user.get('isMailboxSetup', False),
                        'includeInGlobalAddressList': user.get('includeInGlobalAddressList', True)
                    },
                    'name': user.get('name', {}),
                    'admin_info': {
                        'isAdmin': user.get('isAdmin', False),
                        'isDelegatedAdmin': user.get('isDelegatedAdmin', False)
                    },
                    'security_info': {
                        'isEnrolledIn2Sv': user.get('isEnrolledIn2Sv', False),
                        'isEnforcedIn2Sv': user.get('isEnforcedIn2Sv', False)
                    },
                    'organizational_info': {
                        'orgUnitPath': user.get('orgUnitPath', '/')
                    },
                    'contact_info': {
                        'emails': user.get('emails', []),
                        'phones': user.get('phones', []),
                        'recoveryEmail': user.get('recoveryEmail', ''),
                        'recoveryPhone': user.get('recoveryPhone', '')
                    },
                    'profile_info': {
                        'languages': user.get('languages', []),
                        'thumbnailPhotoUrl': user.get('thumbnailPhotoUrl', ''),
                        'thumbnailPhotoEtag': user.get('thumbnailPhotoEtag', '')
                    },
                    'aliases': {
                        'nonEditableAliases': user.get('nonEditableAliases', [])
                    }
                }
            )
            user_resources.append(user_resource)

        # Create GoogleGroupResource objects
        group_resources = []
        for group in groups:
            group_resource = GroupResource(
                id=f"google-group-{group.get('id', '')}",
                source_connector='google',
                group_id=group.get('id', ''),
                group_data={
                    'basic_info': {
                        'kind': group.get('kind', ''),
                        'id': group.get('id', ''),
                        'etag': group.get('etag', ''),
                        'email': group.get('email', ''),
                        'name': group.get('name', ''),
                        'description': group.get('description', ''),
                        'adminCreated': group.get('adminCreated', False)
                    },
                    'membership_info': {
                        'directMembersCount': group.get('directMembersCount', '0')
                    },
                    'aliases': {
                        'nonEditableAliases': group.get('nonEditableAliases', [])
                    }
                }
            )
            group_resources.append(group_resource)

        # Combine all resources
        all_resources = user_resources + group_resources

        # Calculate statistics
        admin_users_count = sum(1 for user in users if user.get('isAdmin', False))
        suspended_users_count = sum(1 for user in users if user.get('suspended', False))
        two_factor_enrolled_users = sum(1 for user in users if user.get('isEnrolledIn2Sv', False))
        two_factor_enforced_users = sum(1 for user in users if user.get('isEnforcedIn2Sv', False))

        # Create GoogleResourceCollection
        resource_collection = GoogleResourceCollection(
            resources=all_resources,
            source_connector='google',
            total_count=len(all_resources),
            fetched_at=datetime.now().isoformat(),
            collection_metadata={
                'total_users': len(users),
                'total_groups': len(groups),
                'admin_users_count': admin_users_count,
                'suspended_users_count': suspended_users_count,
                'two_factor_enrolled_users': two_factor_enrolled_users,
                'two_factor_enforced_users': two_factor_enforced_users,
                'collection_errors': []
            },
            google_api_metadata={
                'collection_time': datetime.now().isoformat(),
                'api_version': 'directory_v1',
                'customer_id': users[0].get('customerId', '') if users else ''
            }
        )

        # Create GoogleInfoData object
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
            groups=[
                {
                    'id': group.get('id', ''),
                    'name': group.get('name', ''),
                    'email': group.get('email', '')
                }
                for group in groups
            ]
        )
        
        return info_data, resource_collection
