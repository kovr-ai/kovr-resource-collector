from providers.provider import Provider, provider_class
from constants import Providers
import boto3

@provider_class
class AWSProvider(Provider):
    def __init__(self, metadata: dict):
        self.AWS_ACCESS_KEY_ID = metadata.get("AWS_ACCESS_KEY_ID")
        self.AWS_SECRET_ACCESS_KEY = metadata.get("AWS_SECRET_ACCESS_KEY")
        self.AWS_SESSION_TOKEN = metadata.get("AWS_SESSION_TOKEN")

        if not self.AWS_ACCESS_KEY_ID or not self.AWS_SECRET_ACCESS_KEY or not self.AWS_SESSION_TOKEN:
            raise ValueError("AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_SESSION_TOKEN are required")

        super().__init__(Providers.AWS.value, metadata)
        
        # Define services to collect data from
        self.services = [
            {"name": "ec2", "class": self._get_service_class("EC2Service")},
            {"name": "iam", "class": self._get_service_class("IAMService")},
            {"name": "s3", "class": self._get_service_class("S3Service")},
            {"name": "cloudtrail", "class": self._get_service_class("CloudTrailService")},
            {"name": "cloudwatch", "class": self._get_service_class("CloudWatchService")}
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
        session = boto3.Session(
            aws_access_key_id=self.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=self.AWS_SECRET_ACCESS_KEY,
            aws_session_token=self.AWS_SESSION_TOKEN,
            region_name="us-east-1"
        )

        self.REGIONS = self.metadata.get("REGIONS") or self._get_all_regions(session)
        self.client = session

    def process(self):
        data = {}
        for region in self.REGIONS:
            print("Fetching data for region: ", region)
            session = boto3.Session(
                aws_access_key_id=self.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=self.AWS_SECRET_ACCESS_KEY,
                aws_session_token=self.AWS_SESSION_TOKEN,
                region_name=region
            )
            for service in self.services:
                print("Fetching data for service: ", service["name"])
                name = service["name"]
                instance = service["class"](session)
                if region not in data:
                    data[region] = {}
                data[region][name] = instance.process()

        return data