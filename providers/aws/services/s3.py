from providers.service import BaseService, service_class
import boto3

@service_class
class S3Service(BaseService):
    def __init__(self, client: boto3.Session):
        super().__init__(client)

    def process(self):
        data = {
            "buckets": {},
            "bucket_policies": {},
            "bucket_encryption": {},
            "bucket_versioning": {},
            "bucket_logging": {},
            "bucket_public_access": {},
            "bucket_lifecycle": {},
            "bucket_notifications": {}
        }
        
        client = self.client.client("s3")

        try:
            response = client.list_buckets()
            for bucket in response["Buckets"]:
                bucket_name = bucket["Name"]
                data["buckets"][bucket_name] = {
                    "creation_date": bucket["CreationDate"].isoformat(),
                    "region": self._get_bucket_region(client, bucket_name)
                }
                
                # Get bucket details
                self._get_bucket_policy(client, bucket_name, data)
                self._get_bucket_encryption(client, bucket_name, data)
                self._get_bucket_versioning(client, bucket_name, data)
                self._get_bucket_logging(client, bucket_name, data)
                self._get_bucket_public_access(client, bucket_name, data)
                self._get_bucket_lifecycle(client, bucket_name, data)
                self._get_bucket_notifications(client, bucket_name, data)
                
        except Exception as e:
            print(f"Error collecting S3 data: {str(e)}")
            data["buckets"] = {}
        
        return data
    
    def _get_bucket_region(self, client, bucket_name):
        """Get bucket region"""
        try:
            response = client.get_bucket_location(Bucket=bucket_name)
            return response.get("LocationConstraint") or "us-east-1"
        except Exception:
            return "unknown"
    
    def _get_bucket_policy(self, client, bucket_name, data):
        """Get bucket policy"""
        try:
            response = client.get_bucket_policy(Bucket=bucket_name)
            data["bucket_policies"][bucket_name] = response["Policy"]
        except client.exceptions.NoSuchBucket:
            data["bucket_policies"][bucket_name] = None
        except Exception:
            data["bucket_policies"][bucket_name] = None
    
    def _get_bucket_encryption(self, client, bucket_name, data):
        """Get bucket encryption configuration"""
        try:
            response = client.get_bucket_encryption(Bucket=bucket_name)
            data["bucket_encryption"][bucket_name] = response["ServerSideEncryptionConfiguration"]
        except client.exceptions.NoSuchBucket:
            data["bucket_encryption"][bucket_name] = None
        except Exception:
            data["bucket_encryption"][bucket_name] = None
    
    def _get_bucket_versioning(self, client, bucket_name, data):
        """Get bucket versioning configuration"""
        try:
            response = client.get_bucket_versioning(Bucket=bucket_name)
            data["bucket_versioning"][bucket_name] = response.get("Status", "NotEnabled")
        except Exception:
            data["bucket_versioning"][bucket_name] = "NotEnabled"
    
    def _get_bucket_logging(self, client, bucket_name, data):
        """Get bucket logging configuration"""
        try:
            response = client.get_bucket_logging(Bucket=bucket_name)
            data["bucket_logging"][bucket_name] = response.get("LoggingEnabled")
        except Exception:
            data["bucket_logging"][bucket_name] = None
    
    def _get_bucket_public_access(self, client, bucket_name, data):
        """Get bucket public access block configuration"""
        try:
            response = client.get_public_access_block(Bucket=bucket_name)
            data["bucket_public_access"][bucket_name] = response["PublicAccessBlockConfiguration"]
        except Exception:
            data["bucket_public_access"][bucket_name] = None
    
    def _get_bucket_lifecycle(self, client, bucket_name, data):
        """Get bucket lifecycle configuration"""
        try:
            response = client.get_bucket_lifecycle_configuration(Bucket=bucket_name)
            data["bucket_lifecycle"][bucket_name] = response["Rules"]
        except client.exceptions.NoSuchBucket:
            data["bucket_lifecycle"][bucket_name] = []
        except Exception:
            data["bucket_lifecycle"][bucket_name] = []
    
    def _get_bucket_notifications(self, client, bucket_name, data):
        """Get bucket notification configuration"""
        try:
            response = client.get_bucket_notification_configuration(Bucket=bucket_name)
            data["bucket_notifications"][bucket_name] = response
        except Exception:
            data["bucket_notifications"][bucket_name] = {} 