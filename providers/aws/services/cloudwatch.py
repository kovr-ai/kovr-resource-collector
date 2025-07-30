from providers.service import BaseService, service_class
import boto3

@service_class
class CloudWatchService(BaseService):
    def __init__(self, client: boto3.Session):
        super().__init__(self)

    def process(self):
        data = {
            "log_groups": {},
            "log_streams": {},
            "metrics": {},
            "alarms": {},
            "dashboards": {}
        }
        
        logs_client = self.client.client("logs")
        cloudwatch_client = self.client.client("cloudwatch")
        
        # Get CloudWatch Logs data
        self._get_log_groups(logs_client, data)
        self._get_log_streams(logs_client, data)
        
        # Get CloudWatch Metrics and Alarms
        self._get_metrics(cloudwatch_client, data)
        self._get_alarms(cloudwatch_client, data)
        self._get_dashboards(cloudwatch_client, data)
        
        return data
    
    def _get_log_groups(self, client, data):
        """Get CloudWatch Log Groups"""
        try:
            paginator = client.get_paginator('describe_log_groups')
            for page in paginator.paginate():
                for log_group in page['logGroups']:
                    log_group_name = log_group["logGroupName"]
                    data["log_groups"][log_group_name] = {
                        "arn": log_group["arn"],
                        "creation_time": log_group.get("creationTime"),
                        "metric_filter_count": log_group.get("metricFilterCount", 0),
                        "stored_bytes": log_group.get("storedBytes", 0),
                        "kms_key_id": log_group.get("kmsKeyId"),
                        "data_protection_status": log_group.get("dataProtectionStatus"),
                        "inherited_properties": log_group.get("inheritedProperties", [])
                    }
        except Exception as e:
            print(f"Error collecting CloudWatch Log Groups: {str(e)}")
            data["log_groups"] = {}
    
    def _get_log_streams(self, client, data):
        """Get CloudWatch Log Streams for each log group"""
        try:
            for log_group_name in data["log_groups"]:
                try:
                    paginator = client.get_paginator('describe_log_streams')
                    streams = []
                    for page in paginator.paginate(logGroupName=log_group_name):
                        for stream in page['logStreams']:
                            streams.append({
                                "log_stream_name": stream["logStreamName"],
                                "creation_time": stream.get("creationTime"),
                                "first_event_time": stream.get("firstEventTime"),
                                "last_event_time": stream.get("lastEventTime"),
                                "last_ingestion_time": stream.get("lastIngestionTime"),
                                "upload_sequence_token": stream.get("uploadSequenceToken"),
                                "arn": stream.get("arn"),
                                "stored_bytes": stream.get("storedBytes", 0)
                            })
                    data["log_streams"][log_group_name] = streams
                except Exception as e:
                    print(f"Error getting log streams for {log_group_name}: {str(e)}")
                    data["log_streams"][log_group_name] = []
        except Exception as e:
            print(f"Error collecting CloudWatch Log Streams: {str(e)}")
            data["log_streams"] = {}
    
    def _get_metrics(self, client, data):
        """Get CloudWatch Metrics"""
        try:
            paginator = client.get_paginator('list_metrics')
            metrics = []
            for page in paginator.paginate():
                for metric in page['Metrics']:
                    metrics.append({
                        "namespace": metric["Namespace"],
                        "metric_name": metric["MetricName"],
                        "dimensions": metric.get("Dimensions", [])
                    })
            data["metrics"] = metrics
        except Exception as e:
            print(f"Error collecting CloudWatch Metrics: {str(e)}")
            data["metrics"] = []
    
    def _get_alarms(self, client, data):
        """Get CloudWatch Alarms"""
        try:
            paginator = client.get_paginator('describe_alarms')
            for page in paginator.paginate():
                for alarm in page['MetricAlarms']:
                    alarm_name = alarm["AlarmName"]
                    data["alarms"][alarm_name] = {
                        "alarm_arn": alarm["AlarmArn"],
                        "alarm_description": alarm.get("AlarmDescription"),
                        "alarm_configuration_updated_timestamp": alarm.get("AlarmConfigurationUpdatedTimestamp"),
                        "actions_enabled": alarm["ActionsEnabled"],
                        "ok_actions": alarm.get("OKActions", []),
                        "alarm_actions": alarm.get("AlarmActions", []),
                        "insufficient_data_actions": alarm.get("InsufficientDataActions", []),
                        "state_value": alarm["StateValue"],
                        "state_reason": alarm.get("StateReason"),
                        "state_reason_data": alarm.get("StateReasonData"),
                        "state_updated_timestamp": alarm["StateUpdatedTimestamp"],
                        "metric_name": alarm["MetricName"],
                        "namespace": alarm["Namespace"],
                        "statistic": alarm["Statistic"],
                        "extended_statistic": alarm.get("ExtendedStatistic"),
                        "period": alarm["Period"],
                        "unit": alarm.get("Unit"),
                        "evaluation_periods": alarm["EvaluationPeriods"],
                        "datapoints_to_alarm": alarm.get("DatapointsToAlarm"),
                        "threshold": alarm["Threshold"],
                        "comparison_operator": alarm["ComparisonOperator"],
                        "treat_missing_data": alarm.get("TreatMissingData"),
                        "evaluate_low_sample_count_percentile": alarm.get("EvaluateLowSampleCountPercentile"),
                        "metrics": alarm.get("Metrics", [])
                    }
        except Exception as e:
            print(f"Error collecting CloudWatch Alarms: {str(e)}")
            data["alarms"] = {}
    
    def _get_dashboards(self, client, data):
        """Get CloudWatch Dashboards"""
        try:
            response = client.list_dashboards()
            for dashboard in response["DashboardEntries"]:
                dashboard_name = dashboard["DashboardName"]
                data["dashboards"][dashboard_name] = {
                    "dashboard_arn": dashboard["DashboardArn"],
                    "dashboard_name": dashboard["DashboardName"],
                    "last_modified": dashboard.get("LastModified"),
                    "size": dashboard.get("Size", 0)
                }
        except Exception as e:
            print(f"Error collecting CloudWatch Dashboards: {str(e)}")
            data["dashboards"] = {} 