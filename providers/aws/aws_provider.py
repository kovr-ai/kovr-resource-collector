from providers.aws.services.cloudtrail import CloudTrailService
from providers.aws.services.cloudwatch import CloudWatchService
from providers.aws.services.ec2 import EC2Service
from providers.aws.services.iam import IAMService
from providers.aws.services.s3 import S3Service
from providers.provider import Provider, provider_class
from constants import Providers
import boto3


@provider_class
class AWSProvider(Provider):
    def __init__(self, metadata: dict):
        self.AWS_ACCESS_KEY_ID = metadata.get("AWS_ACCESS_KEY_ID")
        self.AWS_SECRET_ACCESS_KEY = metadata.get("AWS_SECRET_ACCESS_KEY")
        self.AWS_SESSION_TOKEN = metadata.get("AWS_SESSION_TOKEN")
        self.ROLE_ARN = metadata.get("AWS_ROLE_ARN")
        self.AWS_EXTERNAL_ID = metadata.get("AWS_EXTERNAL_ID")

        if (
            not self.AWS_ACCESS_KEY_ID
            or not self.AWS_SECRET_ACCESS_KEY
            or not self.AWS_SESSION_TOKEN
        ):
            raise ValueError(
                "AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_SESSION_TOKEN are required"
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

    def process(self):
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

        return data
