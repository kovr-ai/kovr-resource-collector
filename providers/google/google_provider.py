from providers.provider import Provider, provider_class
from constants import Providers
from google.oauth2 import service_account
from googleapiclient.discovery import build
import boto3
import json
from con_mon.mappings.google import (
    GoogleInfoData,
    UserResource,
    GroupResource,
    GoogleResourceCollection
)
import os
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
    def __init__(self, metadata: dict):
        self._mock_response_filepath = 'tests/mocks/google/response.json'
        self.use_mock_data = settings.USE_MOCKS and os.path.exists(self._mock_response_filepath)
        super().__init__(Providers.GOOGLE.value, metadata)

    def connect(self):
        # Skip Google connection if using mock data
        if self.use_mock_data:
            print("🔄 Mock mode detected - skipping Google connection")
            return

        service_account_info = self.get_service_account_secret_from_Google()

        credentials = service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=SCOPES,
            subject=self.metadata.get('super_admin_email')
        )

        service = build('admin', 'directory_v1', credentials=credentials)
        return service

    def get_service_account_secret_from_Google(self):
        boto3.setup_default_session(region_name='us-west-2')
        # session = boto3.Session(profile_name=settings.Google_PROFILE)
        # secrets_client = session.client('secretsmanager')
        secrets_client = boto3.client('secretsmanager')
        response = secrets_client.get_secret_value(SecretId=SERVICE_ACCOUNT_SECRET)
        return json.loads(response['SecretString'])

    def _fetch_data(self) -> dict:
        data: dict = dict()
        if self.use_mock_data:
            print("🔄 Collecting mock Google data via test mocks")
            with open(
                    self._mock_response_filepath,
                    'r'
            ) as mock_response_file:
                data = json.load(mock_response_file)
        else:
            # Fetch all users
            results = self.client.users().list(customer='my_customer', maxResults=500, orderBy='email').execute()
            users = results.get('users', [])

            # Fetch all groups
            results = self.client.groups().list(customer='my_customer', maxResults=500, orderBy='email').execute()
            groups = results.get('groups', [])

            for user in users:
                user_id = f"google-user-{user['id']}"
                data['users'][user_id] = user

            for group in groups:
                group_id = f"google-group-{group['id']}"
                data['groups'][group_id] = group

        return data

    def process(self) -> Tuple[GoogleInfoData, GoogleResourceCollection]:

        """Process data collection - uses mock data if available, otherwise real AWS API calls"""
        data: dict = self._fetch_data()
        resource_collection = self._create_resource_collection_from_data(data)
        info_data = self._create_info_data_from_resource_collection(resource_collection)

        return info_data, resource_collection

    def _create_resource_collection_from_data(self, google_data: dict) -> GoogleResourceCollection:
        """Helper method to create GoogleResourceCollection from raw GOOGLE data"""

        # Create GoogleResourceCollection
        user_resources: List[UserResource] = self._create_user_resource_from_data(google_data['users'])
        group_resources: List[GroupResource] = self._create_group_resource_from_data(google_data['groups'])

        # Calculate statistics
        admin_users_count = sum(1 for user in user_resources if user.admin_info.isAdmin)
        suspended_users_count = sum(1 for user in user_resources if user.basic_info.suspended)
        two_factor_enrolled_users = sum(1 for user in user_resources if user.security_info.isEnrolledIn2Sv)

        resource_collection = GoogleResourceCollection(
            resources=user_resources + group_resources,
            source_connector='google',
            total_count=len(user_resources + group_resources),
            fetched_at=datetime.now().isoformat(),
            collection_metadata={
                'total_users': len(user_resources),
                'total_groups': len(group_resources),
                'admin_users_count': admin_users_count,
                'suspended_users_count': suspended_users_count,
                'two_factor_enrolled_users': two_factor_enrolled_users,
                'collection_errors': []
            },
            google_api_metadata={
                'collection_time': datetime.now().isoformat(),
                'api_version': 'directory_v1',
                'customer_id': user_resources[0].basic_info.customerId if user_resources else ''
            }
        )
        return resource_collection

    def _create_user_resource_from_data(self, users_data: dict) -> UserResource:
        user_resources: List[UserResource] = []
        for user_id, user in users_data.items():
            user_resource = UserResource(
                id=user_id,
                source_connector='google',
                user_id=user.get('id', ''),
                **{
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
        return user_resources

    def _create_group_resource_from_data(self, groups_data: dict) -> GroupResource:
        group_resources: List[GroupResource] = []
        for group_id, group in groups_data.items():
            group_resource = GroupResource(
                id=group_id,
                source_connector='google',
                group_id=group.get('id', ''),
                **{
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
        return group_resources

    def _create_info_data_from_resource_collection(
            self,
            resource_collection: GoogleResourceCollection
    ) -> GoogleInfoData:
        users = [
            resource
            for resource in resource_collection.resources
            if isinstance(resource, UserResource)
        ]
        groups = [
            resource
            for resource in resource_collection.resources
            if isinstance(resource, GroupResource)
        ]
        return GoogleInfoData(
            raw_json={
                resource.id: json.loads(resource.model_dump_json())
                for resource in resource_collection.resources
            },
            account_id=self.metadata['super_admin_email'],
            users=[
                {
                    'id': user.id,
                    'name': user.name.fullName,
                    'email': user.basic_info.primaryEmail,
                }
                for user in users
            ],
            groups=[
                {
                    'id': group.id,
                    'name': group.basic_info.name,
                    'email': group.basic_info.email,
                }
                for group in groups
            ]
        )
