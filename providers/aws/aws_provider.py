from providers.aws.services.cloudtrail import CloudTrailService
from providers.aws.services.cloudwatch import CloudWatchService
from providers.aws.services.ec2 import EC2Service
from providers.aws.services.iam import IAMService
from providers.aws.services.s3 import S3Service
from providers.provider import Provider, provider_class
from con_mon.resources import (
    AWSEC2Resource, 
    AWSIAMResource, 
    AWSS3Resource, 
    AWSCloudTrailResource, 
    AWSCloudWatchResource,
    AWSResourceCollection
)
from constants import Providers
import boto3
import json
import os
from datetime import datetime


@provider_class
class AWSProvider(Provider):
    def __init__(self, metadata: dict):
        self.AWS_ACCESS_KEY_ID = metadata.get("AWS_ACCESS_KEY_ID")
        self.AWS_SECRET_ACCESS_KEY = metadata.get("AWS_SECRET_ACCESS_KEY")
        self.AWS_SESSION_TOKEN = metadata.get("AWS_SESSION_TOKEN")
        self.ROLE_ARN = metadata.get("AWS_ROLE_ARN")
        self.AWS_EXTERNAL_ID = metadata.get("AWS_EXTERNAL_ID")
        
        # Check if we should use mock mode (if aws_response.json exists)
        self.use_mock_data = os.path.exists('aws_response.json')
        
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
        client_session = None
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

    def process(self) -> AWSResourceCollection:
        """Process data collection - uses mock data if available, otherwise real AWS API calls"""
        if self.use_mock_data:
            return self._process_mock_data()
        else:
            return self._process_real_aws_data()
    
    def _process_mock_data(self) -> AWSResourceCollection:
        """Load and return mock data from aws_response.json as AWSResourceCollection"""
        print("🔄 Using mock AWS data from aws_response.json")
        
        try:
            with open('aws_response.json', 'r') as mock_response_file:
                mock_response = json.load(mock_response_file)
                
            print(f"✅ Loaded mock AWS data with {len(mock_response)} regions")
            
            # Use the shared helper method to create AWSResourceCollection
            return self._create_resource_collection_from_data(mock_response)
            
        except Exception as e:
            print(f"❌ Error loading mock data: {e}")
            raise RuntimeError(f"Failed to load mock data from aws_response.json: {e}")

    def _process_real_aws_data(self) -> AWSResourceCollection:
        """Original AWS data collection logic using real API calls - returns AWSResourceCollection"""
        print("🔄 Collecting real AWS data via API calls")
        data = {}
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

        # Convert the raw data to AWSResourceCollection using the same logic as mock data
        return self._create_resource_collection_from_data(data)
    
    def _create_resource_collection_from_data(self, aws_data: dict) -> AWSResourceCollection:
        """Helper method to create AWSResourceCollection from raw AWS data"""
        aws_resources = []
        
        # Process each region's data
        for region_name, region_data in aws_data.items():
            try:
                # Create EC2 resource if EC2 data exists
                if 'ec2' in region_data:
                    ec2_data = region_data['ec2']
                    
                    ec2_resource_data = {
                        'region': region_name,
                        'instances': ec2_data.get('instances', {}),
                        'security_groups': ec2_data.get('security_groups', {}),
                        'vpcs': ec2_data.get('vpcs', {}),
                        'subnets': ec2_data.get('subnets', {}),
                        'route_tables': ec2_data.get('route_tables', {}),
                        'nat_gateways': ec2_data.get('nat_gateways', {}),
                        'elastic_ips': ec2_data.get('elastic_ips', {}),
                        'key_pairs': ec2_data.get('key_pairs', {}),
                        'snapshots': ec2_data.get('snapshots', {}),
                        'volumes': ec2_data.get('volumes', {}),
                        'network_interfaces': ec2_data.get('network_interfaces', {}),
                        'internet_gateways': ec2_data.get('internet_gateways', {}),
                        # Use the raw relationships data as-is (now matches schema)
                        'relationships': ec2_data.get('relationships', {}),
                        # Map the account field properly including limits structure
                        'account': ec2_data.get('account', {}),
                        # Add required base Resource fields
                        'id': f"aws-ec2-{region_name}",
                        'source_connector': 'aws'
                    }
                    ec2_resource = AWSEC2Resource(**ec2_resource_data)
                    aws_resources.append(ec2_resource)
                
                # Create IAM resource if IAM data exists
                if 'iam' in region_data:
                    iam_resource_data = {
                        'users': region_data['iam'].get('users', []),
                        'groups': region_data['iam'].get('groups', []),
                        'roles': region_data['iam'].get('roles', []),
                        'policies': region_data['iam'].get('policies', []),
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
                    iam_resource = AWSIAMResource(**iam_resource_data)
                    aws_resources.append(iam_resource)
                
                # Create S3 resource if S3 data exists
                if 's3' in region_data:
                    s3_resource_data = {
                        'buckets': region_data['s3'].get('buckets', []),
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
                    s3_resource = AWSS3Resource(**s3_resource_data)
                    aws_resources.append(s3_resource)
                
                # Create CloudTrail resource if CloudTrail data exists
                if 'cloudtrail' in region_data:
                    cloudtrail_resource_data = {
                        'trails': region_data['cloudtrail'].get('trails', []),
                        'trail_status': region_data['cloudtrail'].get('trail_status', []),
                        'event_selectors': region_data['cloudtrail'].get('event_selectors', []),
                        'insight_selectors': region_data['cloudtrail'].get('insight_selectors', []),
                        'data_events': region_data['cloudtrail'].get('data_events', []),
                        'management_events': region_data['cloudtrail'].get('management_events', []),
                        # Add required base Resource fields
                        'id': f"aws-cloudtrail-{region_name}",
                        'source_connector': 'aws'
                    }
                    cloudtrail_resource = AWSCloudTrailResource(**cloudtrail_resource_data)
                    aws_resources.append(cloudtrail_resource)
                
                # Create CloudWatch resource if CloudWatch data exists
                if 'cloudwatch' in region_data:
                    cloudwatch_resource_data = {
                        'log_groups': region_data['cloudwatch'].get('log_groups', []),
                        'log_streams': region_data['cloudwatch'].get('log_streams', []),
                        'metrics': region_data['cloudwatch'].get('metrics', []),
                        'alarms': region_data['cloudwatch'].get('alarms', []),
                        'dashboards': region_data['cloudwatch'].get('dashboards', []),
                        'retention_policies': region_data['cloudwatch'].get('retention_policies', []),
                        'subscription_filters': region_data['cloudwatch'].get('subscription_filters', []),
                        'metric_filters': region_data['cloudwatch'].get('metric_filters', []),
                        # Add required base Resource fields
                        'id': f"aws-cloudwatch-{region_name}",
                        'source_connector': 'aws'
                    }
                    cloudwatch_resource = AWSCloudWatchResource(**cloudwatch_resource_data)
                    aws_resources.append(cloudwatch_resource)
                    
            except Exception as e:
                print(f"Error converting AWS data for region {region_name}: {e}")
                continue
        
        # Create and return AWSResourceCollection
        return AWSResourceCollection(
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
