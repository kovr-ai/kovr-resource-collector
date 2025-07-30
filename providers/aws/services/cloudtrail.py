from providers.service import BaseService, service_class
import boto3

@service_class
class CloudTrailService(BaseService):
    def __init__(self, client: boto3.Session):
        super().__init__(self)

    def process(self):
        data = {
            "trails": {},
            "event_selectors": {},
            "insight_selectors": {},
            "tags": {}
        }
        
        client = self.client.client("cloudtrail")
        
        try:
            response = client.list_trails()
            for trail in response["trails"]:
                trail_name = trail["Name"]
                trail_arn = trail["TrailARN"]
                
                # Get detailed trail information
                try:
                    trail_response = client.describe_trails(trailNameList=[trail_name])
                    if trail_response["trailList"]:
                        trail_info = trail_response["trailList"][0]
                        data["trails"][trail_name] = {
                            "name": trail_info["Name"],
                            "s3_bucket_name": trail_info.get("S3BucketName"),
                            "s3_key_prefix": trail_info.get("S3KeyPrefix"),
                            "sns_topic_name": trail_info.get("SnsTopicName"),
                            "sns_topic_arn": trail_info.get("SnsTopicARN"),
                            "include_global_service_events": trail_info.get("IncludeGlobalServiceEvents", False),
                            "is_multi_region_trail": trail_info.get("IsMultiRegionTrail", False),
                            "home_region": trail_info.get("HomeRegion"),
                            "trail_arn": trail_info.get("TrailARN"),
                            "log_file_validation_enabled": trail_info.get("LogFileValidationEnabled", False),
                            "cloud_watch_logs_log_group_arn": trail_info.get("CloudWatchLogsLogGroupArn"),
                            "cloud_watch_logs_role_arn": trail_info.get("CloudWatchLogsRoleArn"),
                            "kms_key_id": trail_info.get("KmsKeyId"),
                            "has_custom_event_selectors": trail_info.get("HasCustomEventSelectors", False),
                            "has_insight_selectors": trail_info.get("HasInsightSelectors", False),
                            "is_organization_trail": trail_info.get("IsOrganizationTrail", False)
                        }
                        
                        # Get event selectors
                        self._get_event_selectors(client, trail_name, data)
                        
                        # Get insight selectors
                        self._get_insight_selectors(client, trail_name, data)
                        
                        # Get tags
                        self._get_trail_tags(client, trail_arn, data)
                        
                except Exception as e:
                    print(f"Error getting trail details for {trail_name}: {str(e)}")
                    data["trails"][trail_name] = {}
                    
        except Exception as e:
            print(f"Error collecting CloudTrail data: {str(e)}")
            data["trails"] = {}
        
        return data
    
    def _get_event_selectors(self, client, trail_name, data):
        """Get event selectors for a trail"""
        try:
            response = client.get_event_selectors(TrailName=trail_name)
            data["event_selectors"][trail_name] = response.get("EventSelectors", [])
        except Exception:
            data["event_selectors"][trail_name] = []
    
    def _get_insight_selectors(self, client, trail_name, data):
        """Get insight selectors for a trail"""
        try:
            response = client.get_insight_selectors(TrailName=trail_name)
            data["insight_selectors"][trail_name] = response.get("InsightSelectors", [])
        except Exception:
            data["insight_selectors"][trail_name] = []
    
    def _get_trail_tags(self, client, trail_arn, data):
        """Get tags for a trail"""
        try:
            response = client.list_tags(ResourceIdList=[trail_arn])
            if response["ResourceTagList"]:
                tags = response["ResourceTagList"][0].get("TagsList", [])
                data["tags"][trail_arn] = {tag["Key"]: tag["Value"] for tag in tags}
            else:
                data["tags"][trail_arn] = {}
        except Exception:
            data["tags"][trail_arn] = {} 