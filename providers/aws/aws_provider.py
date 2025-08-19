from providers.aws.services.cloudtrail import CloudTrailService
from providers.aws.services.cloudwatch import CloudWatchService
from providers.aws.services.ec2 import EC2Service
from providers.aws.services.iam import IAMService
from providers.aws.services.s3 import S3Service
from providers.provider import Provider, provider_class
from con_mon.mappings.aws import (
    EC2Resource,
    IAMResource,
    S3Resource,
    CloudTrailResource,
    CloudWatchResource,
    AwsInfoData,
    AwsResourceCollection
)
from typing import Tuple
from constants import Providers
import boto3
import json
import os
from datetime import datetime


def _dict_to_list_with_id(data: dict[str, dict]) -> list[dict]:
    """
    Transform a dictionary of dictionaries to a list of dictionaries,
    where each dictionary key becomes an 'id' field in the value dictionary.

    Args:
        data: Dictionary where keys are strings and values are dictionaries

    Returns:
        List of dictionaries, each containing an 'id' field with the original key
    """
    return [{'id': key, **value} for key, value in data.items()]


@provider_class
class AWSProvider(Provider):
    def __init__(self, metadata: dict):
        self._mock_response_filepath = 'tests/mocks/aws/response.json'
        self.use_mock_data = os.path.exists(self._mock_response_filepath)
        self.AWS_ACCESS_KEY_ID = os.getenv("KOVR_AWS_ACCESS_KEY_ID")
        self.AWS_SECRET_ACCESS_KEY = os.getenv("KOVR_AWS_SECRET_ACCESS_KEY")
        self.AWS_SESSION_TOKEN = os.getenv("AWS_SESSION_TOKEN")
        self.ROLE_ARN = metadata.get("role_arn")
        self.AWS_EXTERNAL_ID = metadata.get("external_id")

        if not self.use_mock_data and (
            not self.AWS_ACCESS_KEY_ID
            or not self.AWS_SECRET_ACCESS_KEY
        ):
            raise ValueError(
                "AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY are required"
            )

        super().__init__(Providers.AWS.value, metadata)

        # Define services to collect data from
        self.services = [
            {"name": "ec2", "class": EC2Service},
            {"name": "iam", "class": IAMService},
            {"name": "s3", "class": S3Service},
            {"name": "cloudtrail", "class": CloudTrailService},
            {"name": "cloudwatch", "class": CloudWatchService},
        ]

    def _get_all_regions(self, session: boto3.Session):
        ec2 = session.client("ec2")
        regions = []
        try:
            response = ec2.describe_regions()
            regions = [region["RegionName"] for region in response["Regions"]]
        except Exception as e:
            print(f"Failed to get regions: {str(e)}")
            regions = []
        return regions

    def connect(self):
        # Skip AWS connection if using mock data
        if self.use_mock_data:
            print("🔄 Mock mode detected - skipping AWS connection")
            self.client = None  # No real client needed for mock data
            self.REGIONS = self.metadata.get("REGIONS", ["us-west-2"])  # Default regions for mock
            return

        # Original AWS connection logic for real API calls
        session_kwargs = {"region_name": "us-east-1"}
        if self.AWS_ACCESS_KEY_ID and self.AWS_SECRET_ACCESS_KEY:
            session_kwargs.update(
                {
                    "aws_access_key_id": self.AWS_ACCESS_KEY_ID,
                    "aws_secret_access_key": self.AWS_SECRET_ACCESS_KEY,
                }
            )
            if (
                self.AWS_SESSION_TOKEN
                and self.AWS_SESSION_TOKEN != ""
                and self.AWS_SESSION_TOKEN != "aws_session_token"
            ):
                session_kwargs["aws_session_token"] = self.AWS_SESSION_TOKEN

        main_session = boto3.Session(**session_kwargs)
        kovr_arn = "arn:aws:iam::296062557786:role/KovrAuditRole"
        kovr_session = self.assume_role(kovr_arn, main_session)
        client_session = self.assume_role(
            self.ROLE_ARN, kovr_session, self.AWS_EXTERNAL_ID
        )
        credentials = client_session.get_credentials()
        self.AWS_ACCESS_KEY_ID = credentials.access_key
        self.AWS_SECRET_ACCESS_KEY = credentials.secret_key
        self.AWS_SESSION_TOKEN = credentials.token

        self.client = client_session or main_session

        self.REGIONS = self.metadata.get("REGIONS") or self._get_all_regions(
            self.client
        )

    def assume_role(
        self, role_arn: str, session: boto3.Session, external_id: str = None
    ) -> boto3.Session:
        sts_client = session.client("sts")
        assumed_role = None
        if external_id:
            assumed_role = sts_client.assume_role(
                RoleArn=role_arn,
                RoleSessionName="kovr-data-collector",
                ExternalId=external_id,
            )
        else:
            assumed_role = sts_client.assume_role(
                RoleArn=role_arn,
                RoleSessionName="kovr-data-collector",
            )
        aws_access_key = assumed_role["Credentials"]["AccessKeyId"]
        aws_secret_key = assumed_role["Credentials"]["SecretAccessKey"]
        aws_session_token = assumed_role["Credentials"]["SessionToken"]
        return boto3.Session(
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            aws_session_token=aws_session_token,
        )

    def _save_mock_data(self, data: dict) -> None:
        print("🔄 Saving mock AWS data")
        with open(
                self._mock_response_filepath,
                'w'
        ) as mock_response_file:
            mock_response_file.write(json.dumps(data, indent=4))

    def _fetch_data(self) -> dict:
        data: dict = dict()
        if self.use_mock_data:
            print("🔄 Collecting mock AWS data via test mocks")
            with open(
                    self._mock_response_filepath,
                    'r'
            ) as mock_response_file:
                data = json.load(mock_response_file)
        else:
            print("🔄 Collecting real AWS data via API calls")
            for region in self.REGIONS:
                print("Fetching data for region: ", region)
                session = boto3.Session(
                    aws_access_key_id=self.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=self.AWS_SECRET_ACCESS_KEY,
                    aws_session_token=self.AWS_SESSION_TOKEN,
                    region_name=region,
                )
                for index, service in enumerate(self.services):
                    print(
                        f"Fetching data for service: {service['name']} ({index + 1}/{len(self.services)})"
                    )
                    name = service["name"]
                    instance = service["class"](session)
                    if region not in data:
                        data[region] = {}
                    data[region][name] = instance.process()
        return data

    def process(self) -> Tuple[AwsInfoData, AwsResourceCollection]:
        """Process data collection - uses mock data if available, otherwise real AWS API calls"""
        data: dict = self._fetch_data()
        resource_collection = self._create_resource_collection_from_data(data)
        info_data = self._create_info_data_from_resource_collection(resource_collection)

        return info_data, resource_collection

    def _normalize_policy_statement(self, statement):
        """
        Normalize policy statement by:
        1. Ensuring Action is always a list - if it's a string, convert to single-item list
        2. Ensuring Resource is always a string - if it's a list, take first item
        """
        if isinstance(statement, dict):
            if 'Action' in statement:
                if isinstance(statement['Action'], str):
                    statement['Action'] = [statement['Action']]
            if 'Resource' in statement:
                if isinstance(statement['Resource'], list):
                    statement['Resource'] = statement['Resource'][0]
        return statement

    def _normalize_policy_document(self, policy_data):
        """
        Normalize policy document by ensuring all statements have Action as a list.
        """
        if not isinstance(policy_data, dict):
            return policy_data

        if 'default_version' in policy_data and isinstance(policy_data['default_version'], dict):
            doc = policy_data['default_version'].get('Document', {})
            if 'Statement' in doc:
                statements = doc['Statement']
                if isinstance(statements, list):
                    doc['Statement'] = [self._normalize_policy_statement(stmt) for stmt in statements]
                else:
                    doc['Statement'] = [self._normalize_policy_statement(statements)]
                policy_data['default_version']['Document'] = doc
        return policy_data

    def _create_resource_collection_from_data(self, aws_data: dict) -> AwsResourceCollection:
        """Helper method to create AwsResourceCollection from raw AWS data"""
        aws_resources = []

        # Process each region's data
        for region_name, region_data in aws_data.items():
            try:
                # Create EC2 resource if EC2 data exists
                if 'ec2' in region_data:
                    ec2_data = region_data['ec2']

                    ec2_resource_data = {
                        'region': region_name,
                        'instances': _dict_to_list_with_id(ec2_data.get('instances', {})),
                        'security_groups': ec2_data.get('security_groups', list()),
                        'vpcs': _dict_to_list_with_id(ec2_data.get('vpcs', {})),
                        'subnets': _dict_to_list_with_id(ec2_data.get('subnets', {})),
                        'route_tables': _dict_to_list_with_id(ec2_data.get('route_tables', {})),
                        'nat_gateways': _dict_to_list_with_id(ec2_data.get('nat_gateways', {})),
                        'elastic_ips': _dict_to_list_with_id(ec2_data.get('elastic_ips', {})),
                        'key_pairs': _dict_to_list_with_id(ec2_data.get('key_pairs', {})),
                        'snapshots': _dict_to_list_with_id(ec2_data.get('snapshots', {})),
                        'volumes': _dict_to_list_with_id(ec2_data.get('volumes', {})),
                        'network_interfaces': _dict_to_list_with_id(ec2_data.get('network_interfaces', {})),
                        'internet_gateways': _dict_to_list_with_id(ec2_data.get('internet_gateways', {})),
                        'relationships': ec2_data.get('relationships', {}),
                        'account': ec2_data.get('account', {}),
                        'id': f"aws-ec2-{region_name}",
                        'source_connector': 'aws'
                    }
                    ec2_resource = EC2Resource(**ec2_resource_data)
                    aws_resources.append(ec2_resource)

                # Create IAM resource if IAM data exists
                if 'iam' in region_data:
                    iam_resource_data = {
                        'users': _dict_to_list_with_id(region_data['iam'].get('users', {})),
                        'policies': [
                            self._normalize_policy_document(policy)
                            for policy in _dict_to_list_with_id(region_data['iam'].get('policies', {}))
                        ],
                        # Keep array fields as is
                        'groups': region_data['iam'].get('groups', []),
                        'roles': region_data['iam'].get('roles', []),
                        'managed_policies': region_data['iam'].get('managed_policies', []),
                        'access_keys': region_data['iam'].get('access_keys', []),
                        'mfa_devices': region_data['iam'].get('mfa_devices', []),
                        'password_policy': region_data['iam'].get('password_policy', {}),
                        'account_summary': region_data['iam'].get('account_summary', {}),
                        'credential_report': region_data['iam'].get('credential_report', []),
                        # Add required base Resource fields
                        'id': f"aws-iam-{region_name}",
                        'source_connector': 'aws'
                    }
                    iam_resource = IAMResource(**iam_resource_data)
                    aws_resources.append(iam_resource)

                # Create S3 resource if S3 data exists
                if 's3' in region_data:
                    s3_resource_data = {
                        'buckets': _dict_to_list_with_id(region_data['s3'].get('buckets', {})),
                        # Keep array fields as is
                        'bucket_policies': region_data['s3'].get('bucket_policies', []),
                        'bucket_acls': region_data['s3'].get('bucket_acls', []),
                        'encryption': region_data['s3'].get('encryption', []),
                        'versioning': region_data['s3'].get('versioning', []),
                        'logging': region_data['s3'].get('logging', []),
                        'lifecycle': region_data['s3'].get('lifecycle', []),
                        'replication': region_data['s3'].get('replication', []),
                        'website': region_data['s3'].get('website', []),
                        'cors': region_data['s3'].get('cors', []),
                        # Add required base Resource fields
                        'id': f"aws-s3-{region_name}",
                        'source_connector': 'aws'
                    }
                    s3_resource = S3Resource(**s3_resource_data)
                    aws_resources.append(s3_resource)

                # Create CloudTrail resource if CloudTrail data exists
                if 'cloudtrail' in region_data:
                    cloudtrail_resource_data = {
                        'trails': _dict_to_list_with_id(region_data['cloudtrail'].get('trails', {})),
                        # Keep array fields as is
                        'trail_status': region_data['cloudtrail'].get('trail_status', []),
                        'event_selectors': [],  # Initialize as empty list
                        'insight_selectors': region_data['cloudtrail'].get('insight_selectors', []),
                        'data_events': region_data['cloudtrail'].get('data_events', []),
                        'management_events': region_data['cloudtrail'].get('management_events', []),
                        # Add required base Resource fields
                        'id': f"aws-cloudtrail-{region_name}",
                        'source_connector': 'aws'
                    }
                    cloudtrail_resource = CloudTrailResource(**cloudtrail_resource_data)
                    aws_resources.append(cloudtrail_resource)

                # Create CloudWatch resource if CloudWatch data exists
                if 'cloudwatch' in region_data:
                    cloudwatch_resource_data = {
                        'log_groups': _dict_to_list_with_id(region_data['cloudwatch'].get('log_groups', {})),
                        'alarms': _dict_to_list_with_id(region_data['cloudwatch'].get('alarms', {})),
                        'dashboards': _dict_to_list_with_id(region_data['cloudwatch'].get('dashboards', {})),
                        # Keep array fields as is
                        'metrics': region_data['cloudwatch'].get('metrics', []),
                        # Add required base Resource fields
                        'id': f"aws-cloudwatch-{region_name}",
                        'source_connector': 'aws'
                    }
                    cloudwatch_resource = CloudWatchResource(**cloudwatch_resource_data)
                    aws_resources.append(cloudwatch_resource)

            except Exception as e:
                print(f"Error converting AWS data for region {region_name}: {e}")
                continue

        # Create and return AwsResourceCollection
        return AwsResourceCollection(
            resources=aws_resources,
            source_connector='aws',
            total_count=len(aws_resources),
            fetched_at=datetime.now().isoformat(),
            collection_metadata={
                'account_id': 'aws-account',
                'regions': list(aws_data.keys()),
                'services_collected': ['ec2', 'iam', 's3', 'cloudtrail', 'cloudwatch'],
                'total_ec2_instances': sum(len(region_data.get('ec2', {}).get('instances', [])) for region_data in aws_data.values()),
                'total_iam_users': sum(len(region_data.get('iam', {}).get('users', [])) for region_data in aws_data.values()),
                'total_s3_buckets': sum(len(region_data.get('s3', {}).get('buckets', [])) for region_data in aws_data.values()),
                'total_cloudtrail_trails': sum(len(region_data.get('cloudtrail', {}).get('trails', [])) for region_data in aws_data.values()),
                'total_cloudwatch_log_groups': sum(len(region_data.get('cloudwatch', {}).get('log_groups', [])) for region_data in aws_data.values())
            }
        )


    def _create_info_data_from_resource_collection(
            self,
            resource_collection: AwsResourceCollection
    ) -> AwsInfoData:
        return AwsInfoData(
            raw_json={
                resource.id: json.loads(resource.model_dump_json())
                for resource in resource_collection.resources
            },
            accounts=[
                {
                    'account_name': f"AWS Account {i + 1}",
                    'account_id': f"AWS Account ID: {i + 1}"
                }
                for i in range(1)
            ]
        )