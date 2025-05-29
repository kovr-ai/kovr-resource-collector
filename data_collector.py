import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import os
import logging
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import requests
import uuid
import re
from azure.identity import ClientSecretCredential
from azure.mgmt.storage import StorageManagementClient

import boto3
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app_config = {
    "dev": {
        "url": "https://dev.kovrai.com/api/v1",
        "role_arn": "arn:aws:iam::296062557786:role/KovrAuditRole",
    },
    "qa": {
        "url": "https://qa.kovrai.com/api/v1",
        "role_arn": "arn:aws:iam::650251729525:role/KovrAuditRole",
    },
    "prod": {
        "url": "https://app.kovrai.com/api/v1",
        "role_arn": "arn:aws:iam::314146328961:role/KovrAuditRole",
    },
}

env = os.environ.get("ENV")


class AWSService:
    def __init__(self, session: boto3.Session):
        self.session = session
        self.name = "service"

    def _is_empty_value(self, value: Any) -> bool:
        """Check if a value is empty (empty string, list, dict, or None)."""
        if value is None:
            return True
        if isinstance(value, (str, list, dict)) and not value:
            return True
        if isinstance(value, dict):
            return all(self._is_empty_value(v) for v in value.values())
        if isinstance(value, list):
            return all(self._is_empty_value(item) for item in value)
        return False

    def _clean_empty_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove all keys with empty values from a dictionary recursively."""
        cleaned = {}
        for key, value in data.items():
            if isinstance(value, dict):
                nested = self._clean_empty_data(value)
                if nested:  # Only add non-empty dictionaries
                    cleaned[key] = nested
            elif not self._is_empty_value(value):
                cleaned[key] = value
        return cleaned

    def generate(self) -> Dict[str, Any]:
        """Base generate method that should be overridden by child classes."""
        pass


class EC2Service(AWSService):
    """
    AWS EC2 Service client wrapper for common EC2 operations.
    Provides simplified access to EC2 instance data and related resources.
    """

    def __init__(self, session: boto3.Session):
        super().__init__(session)
        self.name = "ec2"
        self.client = self.session.client("ec2")

    def get_instances(self) -> Dict[str, Any]:
        """Get all EC2 instances in the current region."""
        try:
            paginator = self.client.get_paginator("describe_instances")
            instances = []

            for page in paginator.paginate():
                for reservation in page["Reservations"]:
                    for instance in reservation["Instances"]:
                        instances.append(self._format_instance_data(instance))

            return {"Instances": instances}
        except Exception as e:
            print(f"Error fetching EC2 instances: {str(e)}")
            return {"Instances": []}

    def get_security_groups(self) -> Dict[str, Any]:
        """Get all security groups in the current region."""
        try:
            return self.client.describe_security_groups()
        except Exception as e:
            print(f"Error fetching security groups: {str(e)}")
            return {"SecurityGroups": []}

    def get_volumes(self) -> Dict[str, Any]:
        """Get all EBS volumes in the current region."""
        try:
            return self.client.describe_volumes()
        except Exception as e:
            print(f"Error fetching volumes: {str(e)}")
            return {"Volumes": []}

    def _format_instance_data(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """Format instance data to include essential information."""
        return {
            "InstanceId": instance["InstanceId"],
            "State": instance["State"]["Name"],
            "InstanceType": instance["InstanceType"],
            "LaunchTime": instance["LaunchTime"],
            "PublicIpAddress": instance.get("PublicIpAddress"),
            "PrivateIpAddress": instance.get("PrivateIpAddress"),
            "SecurityGroups": instance.get("SecurityGroups", []),
            "Tags": instance.get("Tags", []),
        }

    def generate(self) -> Dict[str, Any]:
        """Generate a comprehensive report of EC2 resources."""
        data = {
            "instances": self.get_instances(),
            "security_groups": self.get_security_groups(),
            "volumes": self.get_volumes(),
        }
        return data


class IAMService(AWSService):
    """
    AWS IAM Service client wrapper for common IAM operations.
    Provides simplified access to IAM resources and configurations.
    """

    def __init__(self, session: boto3.Session):
        super().__init__(session)
        self.name = "iam"
        self.client = self.session.client("iam")

    def get_users(self) -> Dict[str, Any]:
        """Get all IAM users."""
        try:
            paginator = self.client.get_paginator("list_users")
            users = []
            for page in paginator.paginate():
                users.extend(page["Users"])
            return {"Users": users}
        except Exception as e:
            print(f"Error fetching IAM users: {str(e)}")
            return {"Users": []}

    def get_roles(self) -> Dict[str, Any]:
        """Get all IAM roles."""
        try:
            paginator = self.client.get_paginator("list_roles")
            roles = []
            for page in paginator.paginate():
                roles.extend(page["Roles"])
            return {"Roles": roles}
        except Exception as e:
            print(f"Error fetching IAM roles: {str(e)}")
            return {"Roles": []}

    def get_policies(self) -> Dict[str, Any]:
        """Get customer managed IAM policies."""
        try:
            paginator = self.client.get_paginator("list_policies")
            policies = []
            for page in paginator.paginate(Scope="Local"):
                policies.extend(page["Policies"])
            return {"Policies": policies}
        except Exception as e:
            print(f"Error fetching IAM policies: {str(e)}")
            return {"Policies": []}

    def get_credential_report(self) -> Dict[str, Any]:
        """Get IAM credential report."""
        try:
            self.client.generate_credential_report()
            report = self.client.get_credential_report()
            return {"CredentialReport": report["Content"].decode("utf-8")}
        except Exception as e:
            print(f"Error fetching credential report: {str(e)}")
            return {"CredentialReport": None}

    def generate(self) -> Dict[str, Any]:
        """Generate a comprehensive report of IAM resources."""
        return {
            "users": self.get_users(),
            "roles": self.get_roles(),
            "policies": self.get_policies(),
            "credential_report": self.get_credential_report(),
        }


class KMSService(AWSService):
    """
    AWS KMS Service client wrapper for key management operations.
    Provides simplified access to KMS keys and their configurations.
    """

    def __init__(self, session: boto3.Session):
        super().__init__(session)
        self.name = "kms"
        self.client = self.session.client("kms")

    def get_keys(self) -> Dict[str, Any]:
        """Get all KMS keys and their configurations."""
        try:
            paginator = self.client.get_paginator("list_keys")
            keys = []
            for page in paginator.paginate():
                for key in page["Keys"]:
                    key_detail = self._get_key_details(key["KeyId"])
                    if key_detail:
                        keys.append(key_detail)
            return {"Keys": keys}
        except Exception as e:
            print(f"Error fetching KMS keys: {str(e)}")
            return {"Keys": []}

    def _get_key_details(self, key_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific KMS key."""
        try:
            key_metadata = self.client.describe_key(KeyId=key_id)["KeyMetadata"]
            key_rotation = self._get_key_rotation_status(key_id)

            return {
                "KeyId": key_metadata["KeyId"],
                "Arn": key_metadata["Arn"],
                "KeyState": key_metadata["KeyState"],
                "KeyManager": key_metadata["KeyManager"],
                "Description": key_metadata.get("Description", ""),
                "Enabled": key_metadata["Enabled"],
                "RotationEnabled": key_rotation.get("KeyRotationEnabled", False),
            }
        except Exception as e:
            print(f"Error fetching key details for {key_id}: {str(e)}")
            return None

    def _get_key_rotation_status(self, key_id: str) -> Dict[str, Any]:
        """Get key rotation status for a specific KMS key."""
        try:
            return self.client.get_key_rotation_status(KeyId=key_id)
        except Exception:
            return {}

    def get_aliases(self) -> Dict[str, Any]:
        """Get all KMS key aliases."""
        try:
            paginator = self.client.get_paginator("list_aliases")
            aliases = []
            for page in paginator.paginate():
                aliases.extend(page["Aliases"])
            return {"Aliases": aliases}
        except Exception as e:
            print(f"Error fetching KMS aliases: {str(e)}")
            return {"Aliases": []}

    def generate(self) -> Dict[str, Any]:
        """Generate a comprehensive report of KMS resources."""
        return {"keys": self.get_keys(), "aliases": self.get_aliases()}


class S3Service(AWSService):
    """
    AWS S3 Service client wrapper for common S3 operations.
    Provides simplified access to S3 buckets and their configurations.
    """

    def __init__(self, session: boto3.Session):
        super().__init__(session)
        self.name = "s3"
        self.client = self.session.client("s3")

    def get_buckets(self) -> Dict[str, Any]:
        """Get all S3 buckets and their basic information."""
        try:
            buckets = self.client.list_buckets()["Buckets"]
            return {"Buckets": [self._get_bucket_details(bucket) for bucket in buckets]}
        except Exception as e:
            print(f"Error fetching S3 buckets: {str(e)}")
            return {"Buckets": []}

    def _get_bucket_details(self, bucket: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed information about a specific bucket."""
        try:
            bucket_name = bucket["Name"]
            details = {
                "Name": bucket_name,
                "CreationDate": bucket["CreationDate"],
                "PublicAccessBlock": self._get_public_access_block(bucket_name),
                "Encryption": self._get_encryption(bucket_name),
                "Versioning": self._get_versioning(bucket_name),
                "Policy": self._get_bucket_policy(bucket_name),
            }
            return details
        except Exception as e:
            print(f"Error fetching bucket details for {bucket['Name']}: {str(e)}")
            return bucket

    def _get_public_access_block(self, bucket_name: str) -> Dict[str, Any]:
        """Get public access block configuration for a bucket."""
        try:
            return self.client.get_public_access_block(Bucket=bucket_name)[
                "PublicAccessBlockConfiguration"
            ]
        except Exception:
            return {}

    def _get_encryption(self, bucket_name: str) -> Dict[str, Any]:
        """Get encryption configuration for a bucket."""
        try:
            return self.client.get_bucket_encryption(Bucket=bucket_name)[
                "ServerSideEncryptionConfiguration"
            ]
        except Exception:
            return {}

    def _get_versioning(self, bucket_name: str) -> Dict[str, Any]:
        """Get versioning configuration for a bucket."""
        try:
            return self.client.get_bucket_versioning(Bucket=bucket_name)
        except Exception:
            return {}

    def _get_bucket_policy(self, bucket_name: str) -> Dict[str, Any]:
        """Get bucket policy if it exists."""
        try:
            return self.client.get_bucket_policy(Bucket=bucket_name)["Policy"]
        except Exception:
            return {}

    def generate(self) -> Dict[str, Any]:
        """Generate a comprehensive report of S3 resources."""
        return {"buckets": self.get_buckets()}


class CloudTrailService(AWSService):
    """
    AWS CloudTrail Service client wrapper for trail operations.
    Provides simplified access to CloudTrail configurations and logs.
    """

    def __init__(self, session: boto3.Session):
        super().__init__(session)
        self.name = "cloudtrail"
        self.client = self.session.client("cloudtrail")

    def get_trails(self) -> Dict[str, Any]:
        """Get all CloudTrail trails and their configurations."""
        try:
            trails = self.client.describe_trails()["trailList"]
            return {"Trails": [self._get_trail_status(trail) for trail in trails]}
        except Exception as e:
            print(f"Error fetching CloudTrail trails: {str(e)}")
            return {"Trails": []}

    def _get_trail_status(self, trail: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed status for a specific trail."""
        try:
            trail_name = trail["Name"]
            status = self.client.get_trail_status(Name=trail_name)
            trail.update(
                {
                    "Status": {
                        "IsLogging": status["IsLogging"],
                        "LatestDeliveryTime": status.get("LatestDeliveryTime"),
                        "LatestDeliveryError": status.get("LatestDeliveryError"),
                    }
                }
            )
            return trail
        except Exception as e:
            print(f"Error fetching trail status for {trail['Name']}: {str(e)}")
            return trail

    def get_event_selectors(self) -> Dict[str, Any]:
        """Get event selectors for all trails."""
        try:
            trails = self.client.describe_trails()["trailList"]
            event_selectors = {}
            for trail in trails:
                try:
                    selectors = self.client.get_event_selectors(
                        TrailName=trail["TrailARN"]
                    )
                    event_selectors[trail["Name"]] = selectors
                except Exception:
                    continue
            return {"EventSelectors": event_selectors}
        except Exception as e:
            print(f"Error fetching event selectors: {str(e)}")
            return {"EventSelectors": {}}

    def generate(self) -> Dict[str, Any]:
        """Generate a comprehensive report of CloudTrail resources."""
        return {
            "trails": self.get_trails(),
            "event_selectors": self.get_event_selectors(),
        }


class RDSService(AWSService):
    """
    AWS RDS Service client wrapper for database operations.
    Provides simplified access to RDS instances and their configurations.
    """

    def __init__(self, session: boto3.Session):
        super().__init__(session)
        self.name = "rds"
        self.client = self.session.client("rds")

    def get_db_instances(self) -> Dict[str, Any]:
        """Get all RDS instances and their configurations."""
        try:
            paginator = self.client.get_paginator("describe_db_instances")
            instances = []
            for page in paginator.paginate():
                for instance in page["DBInstances"]:
                    instances.append(self._format_db_instance(instance))
            return {"DBInstances": instances}
        except Exception as e:
            print(f"Error fetching RDS instances: {str(e)}")
            return {"DBInstances": []}

    def _format_db_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """Format RDS instance data to include essential information."""
        return {
            "DBInstanceIdentifier": instance["DBInstanceIdentifier"],
            "Engine": instance["Engine"],
            "EngineVersion": instance["EngineVersion"],
            "DBInstanceClass": instance["DBInstanceClass"],
            "PubliclyAccessible": instance["PubliclyAccessible"],
            "StorageEncrypted": instance["StorageEncrypted"],
            "MultiAZ": instance["MultiAZ"],
            "AutoMinorVersionUpgrade": instance["AutoMinorVersionUpgrade"],
            "BackupRetentionPeriod": instance["BackupRetentionPeriod"],
            "VpcSecurityGroups": instance["VpcSecurityGroups"],
            "Tags": self._get_instance_tags(instance["DBInstanceArn"]),
        }

    def _get_instance_tags(self, instance_arn: str) -> List[Dict[str, str]]:
        """Get tags for a specific RDS instance."""
        try:
            response = self.client.list_tags_for_resource(ResourceName=instance_arn)
            return response.get("TagList", [])
        except Exception:
            return []

    def get_snapshots(self) -> Dict[str, Any]:
        """Get all RDS snapshots."""
        try:
            paginator = self.client.get_paginator("describe_db_snapshots")
            snapshots = []
            for page in paginator.paginate():
                for snapshot in page["DBSnapshots"]:
                    snapshots.append(
                        {
                            "DBSnapshotIdentifier": snapshot["DBSnapshotIdentifier"],
                            "DBInstanceIdentifier": snapshot["DBInstanceIdentifier"],
                            "SnapshotType": snapshot["SnapshotType"],
                            "Encrypted": snapshot["Encrypted"],
                            "Status": snapshot["Status"],
                        }
                    )
            return {"DBSnapshots": snapshots}
        except Exception as e:
            print(f"Error fetching RDS snapshots: {str(e)}")
            return {"DBSnapshots": []}

    def generate(self) -> Dict[str, Any]:
        """Generate a comprehensive report of RDS resources."""
        return {"instances": self.get_db_instances(), "snapshots": self.get_snapshots()}


class VPCService(AWSService):
    def __init__(self, session):
        super().__init__(session)
        self.name = "vpc"
        self.client = self.session.client("ec2")

    def generate(self) -> Dict[str, Any]:
        try:
            vpc_data = {
                "vpcs": [],
                "subnets": [],
                "security_groups": [],
                "route_tables": [],
                "internet_gateways": [],
            }

            # Get VPCs
            vpcs = self.client.describe_vpcs()["Vpcs"]
            vpc_data["vpcs"] = [
                {
                    "id": vpc["VpcId"],
                    "cidr": vpc.get("CidrBlock"),
                    "is_default": vpc.get("IsDefault", False),
                    "state": vpc.get("State"),
                    "tags": vpc.get("Tags", []),
                }
                for vpc in vpcs
            ]

            # Get Subnets
            subnets = self.client.describe_subnets()["Subnets"]
            vpc_data["subnets"] = [
                {
                    "id": subnet["SubnetId"],
                    "vpc_id": subnet["VpcId"],
                    "cidr": subnet["CidrBlock"],
                    "availability_zone": subnet["AvailabilityZone"],
                    "tags": subnet.get("Tags", []),
                }
                for subnet in subnets
            ]

            # Get Security Groups
            sgs = self.client.describe_security_groups()["SecurityGroups"]
            vpc_data["security_groups"] = [
                {
                    "id": sg["GroupId"],
                    "name": sg["GroupName"],
                    "vpc_id": sg["VpcId"],
                    "description": sg["Description"],
                    "inbound_rules": sg["IpPermissions"],
                    "outbound_rules": sg["IpPermissionsEgress"],
                }
                for sg in sgs
            ]

            # Get Route Tables
            route_tables = self.client.describe_route_tables()["RouteTables"]
            vpc_data["route_tables"] = [
                {
                    "id": rt["RouteTableId"],
                    "vpc_id": rt["VpcId"],
                    "routes": rt["Routes"],
                    "associations": rt["Associations"],
                }
                for rt in route_tables
            ]

            # Get Internet Gateways
            igws = self.client.describe_internet_gateways()["InternetGateways"]
            vpc_data["internet_gateways"] = [
                {"id": igw["InternetGatewayId"], "attachments": igw["Attachments"]}
                for igw in igws
            ]

            return vpc_data

        except ClientError as e:
            self.handle_error(e)
            return None


class LambdaService(AWSService):
    def __init__(self, session):
        super().__init__(session)
        self.name = "lambda"
        self.client = self.session.client("lambda")

    def generate(self) -> Dict[str, Any]:
        try:
            lambda_data = {"functions": [], "layers": []}

            # Get Lambda Functions
            paginator = self.client.get_paginator("list_functions")
            for page in paginator.paginate():
                for function in page["Functions"]:
                    function_data = {
                        "name": function["FunctionName"],
                        "arn": function["FunctionArn"],
                        "runtime": function.get("Runtime"),
                        "handler": function.get("Handler"),
                        "role": function.get("Role"),
                        "memory": function.get("MemorySize"),
                        "timeout": function.get("Timeout"),
                        "last_modified": str(function.get("LastModified")),
                        "environment": function.get("Environment", {}).get(
                            "Variables", {}
                        ),
                        "vpc_config": function.get("VpcConfig", {}),
                        "tags": function.get("Tags", {}),
                    }
                    lambda_data["functions"].append(function_data)

            # Get Lambda Layers
            paginator = self.client.get_paginator("list_layers")
            for page in paginator.paginate():
                for layer in page["Layers"]:
                    layer_data = {
                        "name": layer["LayerName"],
                        "arn": layer["LayerArn"],
                        "latest_version": layer.get("LatestMatchingVersion", {}),
                    }
                    lambda_data["layers"].append(layer_data)

            return lambda_data

        except ClientError as e:
            self.handle_error(e)
            return None


class ECSService(AWSService):
    def __init__(self, session):
        super().__init__(session)
        self.name = "ecs"
        self.client = self.session.client("ecs")

    def generate(self) -> Dict[str, Any]:
        try:
            ecs_data = {"clusters": [], "task_definitions": [], "services": []}

            # Get ECS Clusters
            clusters = self.client.list_clusters()["clusterArns"]
            if clusters:
                cluster_details = self.client.describe_clusters(clusters=clusters)[
                    "clusters"
                ]
                ecs_data["clusters"] = [
                    {
                        "name": cluster["clusterName"],
                        "arn": cluster["clusterArn"],
                        "status": cluster["status"],
                        "registered_container_instances_count": cluster.get(
                            "registeredContainerInstancesCount", 0
                        ),
                        "running_tasks_count": cluster.get("runningTasksCount", 0),
                        "pending_tasks_count": cluster.get("pendingTasksCount", 0),
                        "active_services_count": cluster.get("activeServicesCount", 0),
                        "tags": cluster.get("tags", []),
                    }
                    for cluster in cluster_details
                ]

                # Get Services for each cluster
                for cluster in clusters:
                    services = self.client.list_services(cluster=cluster)["serviceArns"]
                    if services:
                        service_details = self.client.describe_services(
                            cluster=cluster, services=services
                        )["services"]
                        for service in service_details:
                            service_data = {
                                "name": service["serviceName"],
                                "arn": service["serviceArn"],
                                "cluster_arn": service["clusterArn"],
                                "status": service["status"],
                                "desired_count": service["desiredCount"],
                                "running_count": service["runningCount"],
                                "pending_count": service["pendingCount"],
                                "task_definition": service["taskDefinition"],
                                "launch_type": service.get("launchType"),
                                "platform_version": service.get("platformVersion"),
                                "tags": service.get("tags", []),
                            }
                            ecs_data["services"].append(service_data)

            # Get Task Definitions
            task_defs = self.client.list_task_definitions()["taskDefinitionArns"]
            if task_defs:
                for task_def_arn in task_defs:
                    task_def = self.client.describe_task_definition(
                        taskDefinition=task_def_arn
                    )["taskDefinition"]
                    task_def_data = {
                        "family": task_def["family"],
                        "revision": task_def["revision"],
                        "arn": task_def["taskDefinitionArn"],
                        "status": task_def["status"],
                        "container_definitions": task_def["containerDefinitions"],
                        "cpu": task_def.get("cpu"),
                        "memory": task_def.get("memory"),
                        "network_mode": task_def.get("networkMode"),
                        "requires_compatibilities": task_def.get(
                            "requiresCompatibilities", []
                        ),
                    }
                    ecs_data["task_definitions"].append(task_def_data)

            return ecs_data

        except ClientError as e:
            self.handle_error(e)
            return None


class SNSService(AWSService):
    def __init__(self, session):
        super().__init__(session)
        self.name = "sns"
        self.client = self.session.client("sns")

    def generate(self) -> Dict[str, Any]:
        try:
            sns_data = {"topics": [], "subscriptions": []}

            # Get SNS Topics
            paginator = self.client.get_paginator("list_topics")
            for page in paginator.paginate():
                for topic in page["Topics"]:
                    topic_arn = topic["TopicArn"]
                    topic_data = {
                        "arn": topic_arn,
                        "name": topic_arn.split(":")[-1],
                        "attributes": self.client.get_topic_attributes(
                            TopicArn=topic_arn
                        )["Attributes"],
                        "tags": self.client.list_tags_for_resource(
                            ResourceArn=topic_arn
                        ).get("Tags", []),
                    }

                    # Get subscriptions for this topic
                    subs_paginator = self.client.get_paginator(
                        "list_subscriptions_by_topic"
                    )
                    topic_subscriptions = []
                    for subs_page in subs_paginator.paginate(TopicArn=topic_arn):
                        for sub in subs_page["Subscriptions"]:
                            sub_data = {
                                "arn": sub["SubscriptionArn"],
                                "protocol": sub["Protocol"],
                                "endpoint": sub["Endpoint"],
                                "owner": sub["Owner"],
                                "topic_arn": sub["TopicArn"],
                            }
                            if sub["SubscriptionArn"] != "PendingConfirmation":
                                try:
                                    attrs = self.client.get_subscription_attributes(
                                        SubscriptionArn=sub["SubscriptionArn"]
                                    )["Attributes"]
                                    sub_data["attributes"] = attrs
                                except ClientError:
                                    pass
                            topic_subscriptions.append(sub_data)

                    topic_data["subscriptions"] = topic_subscriptions
                    sns_data["topics"].append(topic_data)

            return sns_data

        except ClientError as e:
            self.handle_error(e)
            return None


class SQSService(AWSService):
    def __init__(self, session):
        super().__init__(session)
        self.name = "sqs"
        self.client = self.session.client("sqs")

    def generate(self) -> Dict[str, Any]:
        try:
            sqs_data = {"queues": []}

            # Get SQS Queues
            queues = self.client.list_queues()
            if "QueueUrls" in queues:
                for queue_url in queues["QueueUrls"]:
                    queue_data = {
                        "url": queue_url,
                        "name": queue_url.split("/")[-1],
                        "attributes": self.client.get_queue_attributes(
                            QueueUrl=queue_url, AttributeNames=["All"]
                        )["Attributes"],
                        "tags": self.client.list_queue_tags(QueueUrl=queue_url).get(
                            "Tags", {}
                        ),
                    }

                    # Get dead-letter queue if configured
                    if "RedrivePolicy" in queue_data["attributes"]:
                        queue_data["dead_letter_queue"] = queue_data["attributes"][
                            "RedrivePolicy"
                        ]

                    # Get encryption details if configured
                    if "KmsMasterKeyId" in queue_data["attributes"]:
                        queue_data["encryption"] = {
                            "kms_master_key_id": queue_data["attributes"][
                                "KmsMasterKeyId"
                            ],
                            "kms_data_key_reuse_period": queue_data["attributes"].get(
                                "KmsDataKeyReusePeriodSeconds"
                            ),
                        }

                    sqs_data["queues"].append(queue_data)

            return sqs_data

        except ClientError as e:
            self.handle_error(e)
            return None


class ACMService(AWSService):
    def __init__(self, session):
        super().__init__(session)
        self.name = "acm"
        self.client = self.session.client("acm")

    def generate(self) -> Dict[str, Any]:
        try:
            acm_data = {"certificates": []}

            # List certificates
            paginator = self.client.get_paginator("list_certificates")
            for page in paginator.paginate():
                for cert in page["CertificateSummaryList"]:
                    cert_details = self.client.describe_certificate(
                        CertificateArn=cert["CertificateArn"]
                    )["Certificate"]

                    cert_data = {
                        "arn": cert_details["CertificateArn"],
                        "domain_name": cert_details.get("DomainName"),
                        "status": cert_details.get("Status"),
                        "type": cert_details.get("Type"),
                        "subject_alternative_names": cert_details.get(
                            "SubjectAlternativeNames", []
                        ),
                        "domain_validation_options": cert_details.get(
                            "DomainValidationOptions", []
                        ),
                        "issued_at": str(cert_details.get("IssuedAt", "")),
                        "not_before": str(cert_details.get("NotBefore", "")),
                        "not_after": str(cert_details.get("NotAfter", "")),
                        "key_algorithm": cert_details.get("KeyAlgorithm"),
                        "serial_number": cert_details.get("Serial"),
                        "renewal_eligibility": cert_details.get("RenewalEligibility"),
                        "tags": self.client.list_tags_for_certificate(
                            CertificateArn=cert["CertificateArn"]
                        ).get("Tags", []),
                    }
                    acm_data["certificates"].append(cert_data)

            return acm_data

        except ClientError as e:
            self.handle_error(e)
            return None


class DynamoDBService(AWSService):
    def __init__(self, session):
        super().__init__(session)
        self.name = "dynamodb"
        self.client = self.session.client("dynamodb")

    def generate(self) -> Dict[str, Any]:
        try:
            dynamodb_data = {"tables": [], "backups": [], "global_tables": []}

            # List tables
            paginator = self.client.get_paginator("list_tables")
            for page in paginator.paginate():
                for table_name in page["TableNames"]:
                    table = self.client.describe_table(TableName=table_name)["Table"]
                    table_data = {
                        "name": table["TableName"],
                        "arn": table.get("TableArn"),
                        "status": table.get("TableStatus"),
                        "creation_date": str(table.get("CreationDateTime", "")),
                        "provisioned_throughput": table.get(
                            "ProvisionedThroughput", {}
                        ),
                        "size_bytes": table.get("TableSizeBytes"),
                        "item_count": table.get("ItemCount"),
                        "key_schema": table.get("KeySchema", []),
                        "attribute_definitions": table.get("AttributeDefinitions", []),
                        "billing_mode": table.get("BillingModeSummary", {}).get(
                            "BillingMode"
                        ),
                        "encryption": table.get("SSEDescription", {}),
                        "tags": self.client.list_tags_of_resource(
                            ResourceArn=table["TableArn"]
                        ).get("Tags", []),
                    }

                    # Get continuous backups status
                    try:
                        backup_status = self.client.describe_continuous_backups(
                            TableName=table_name
                        )
                        table_data["continuous_backups"] = backup_status.get(
                            "ContinuousBackupsDescription", {}
                        )
                    except ClientError:
                        pass

                    dynamodb_data["tables"].append(table_data)

            # List backups
            try:
                backups = self.client.list_backups()
                dynamodb_data["backups"] = [
                    {
                        "arn": backup["BackupArn"],
                        "name": backup["BackupName"],
                        "status": backup["BackupStatus"],
                        "creation_date": str(backup.get("BackupCreationDateTime", "")),
                        "size_bytes": backup.get("BackupSizeBytes"),
                        "table_name": backup.get("TableName"),
                        "table_id": backup.get("TableId"),
                    }
                    for backup in backups.get("BackupSummaries", [])
                ]
            except ClientError:
                pass

            # List global tables
            try:
                global_tables = self.client.list_global_tables()
                dynamodb_data["global_tables"] = [
                    {
                        "name": table["GlobalTableName"],
                        "replication_group": table.get("ReplicationGroup", []),
                        "status": table.get("GlobalTableStatus"),
                    }
                    for table in global_tables.get("GlobalTables", [])
                ]
            except ClientError:
                pass

            return dynamodb_data

        except ClientError as e:
            self.handle_error(e)
            return None


class EKSService(AWSService):
    def __init__(self, session):
        super().__init__(session)
        self.name = "eks"
        self.client = self.session.client("eks")

    def generate(self) -> Dict[str, Any]:
        try:
            eks_data = {"clusters": []}

            # List clusters
            clusters = self.client.list_clusters()["clusters"]
            for cluster_name in clusters:
                cluster = self.client.describe_cluster(name=cluster_name)["cluster"]

                # Get nodegroups for this cluster
                nodegroups = self.client.list_nodegroups(clusterName=cluster_name)[
                    "nodegroups"
                ]
                nodegroup_details = []

                for nodegroup_name in nodegroups:
                    nodegroup = self.client.describe_nodegroup(
                        clusterName=cluster_name, nodegroupName=nodegroup_name
                    )["nodegroup"]

                    nodegroup_data = {
                        "name": nodegroup["nodegroupName"],
                        "arn": nodegroup["nodegroupArn"],
                        "status": nodegroup["status"],
                        "instance_types": nodegroup.get("instanceTypes", []),
                        "subnets": nodegroup.get("subnets", []),
                        "scaling_config": nodegroup.get("scalingConfig", {}),
                        "disk_size": nodegroup.get("diskSize"),
                        "capacity_type": nodegroup.get("capacityType"),
                        "ami_type": nodegroup.get("amiType"),
                        "remote_access": nodegroup.get("remoteAccess", {}),
                        "tags": nodegroup.get("tags", {}),
                    }
                    nodegroup_details.append(nodegroup_data)

                # Get Fargate profiles for this cluster
                try:
                    fargate_profiles = self.client.list_fargate_profiles(
                        clusterName=cluster_name
                    )["fargateProfileNames"]
                    fargate_details = []

                    for profile_name in fargate_profiles:
                        profile = self.client.describe_fargate_profile(
                            clusterName=cluster_name, fargateProfileName=profile_name
                        )["fargateProfile"]

                        profile_data = {
                            "name": profile["fargateProfileName"],
                            "arn": profile["fargateProfileArn"],
                            "status": profile["status"],
                            "pod_execution_role_arn": profile.get(
                                "podExecutionRoleArn"
                            ),
                            "subnets": profile.get("subnets", []),
                            "selectors": profile.get("selectors", []),
                            "tags": profile.get("tags", {}),
                        }
                        fargate_details.append(profile_data)
                except ClientError:
                    fargate_details = []

                cluster_data = {
                    "name": cluster["name"],
                    "arn": cluster["arn"],
                    "status": cluster["status"],
                    "endpoint": cluster.get("endpoint"),
                    "version": cluster.get("version"),
                    "role_arn": cluster.get("roleArn"),
                    "vpc_config": cluster.get("resourcesVpcConfig", {}),
                    "logging": cluster.get("logging", {}),
                    "identity": cluster.get("identity", {}),
                    "status": cluster.get("status"),
                    "certificate_authority": cluster.get("certificateAuthority", {}),
                    "kubernetes_network_config": cluster.get(
                        "kubernetesNetworkConfig", {}
                    ),
                    "encryption_config": cluster.get("encryptionConfig", []),
                    "nodegroups": nodegroup_details,
                    "fargate_profiles": fargate_details,
                    "tags": cluster.get("tags", {}),
                }
                eks_data["clusters"].append(cluster_data)

            return eks_data

        except ClientError as e:
            self.handle_error(e)
            return None


class ElastiCacheService(AWSService):
    def __init__(self, session):
        super().__init__(session)
        self.name = "elasticache"
        self.client = self.session.client("elasticache")

    def generate(self) -> Dict[str, Any]:
        try:
            elasticache_data = {"clusters": [], "replication_groups": []}

            # List clusters
            try:
                paginator = self.client.get_paginator("describe_cache_clusters")
                for page in paginator.paginate():
                    for cluster in page.get("CacheClusters", []):
                        cluster_data = {
                            "id": cluster["CacheClusterId"],
                            "status": cluster["CacheClusterStatus"],
                            "node_type": cluster.get("CacheNodeType"),
                            "engine": cluster.get("Engine"),
                            "engine_version": cluster.get("EngineVersion"),
                            "num_cache_nodes": cluster.get("NumCacheNodes"),
                            "preferred_availability_zone": cluster.get(
                                "PreferredAvailabilityZone"
                            ),
                            "security_groups": [
                                sg["SecurityGroupId"]
                                for sg in cluster.get("SecurityGroups", [])
                            ],
                            "encryption": {
                                "at_rest": cluster.get("AtRestEncryptionEnabled"),
                                "in_transit": cluster.get("TransitEncryptionEnabled"),
                            },
                            "tags": self.client.list_tags_for_resource(
                                ResourceName=cluster["ARN"]
                            ).get("TagList", []),
                        }
                        elasticache_data["clusters"].append(cluster_data)
            except ClientError:
                pass

            # List replication groups
            try:
                paginator = self.client.get_paginator("describe_replication_groups")
                for page in paginator.paginate():
                    for group in page.get("ReplicationGroups", []):
                        group_data = {
                            "id": group["ReplicationGroupId"],
                            "description": group.get("Description"),
                            "status": group["Status"],
                            "member_clusters": group.get("MemberClusters", []),
                            "automatic_failover": group.get("AutomaticFailover"),
                            "multi_az": group.get("MultiAZ"),
                            "tags": self.client.list_tags_for_resource(
                                ResourceName=group["ARN"]
                            ).get("TagList", []),
                        }
                        elasticache_data["replication_groups"].append(group_data)
            except ClientError:
                pass

            return elasticache_data

        except ClientError as e:
            self.handle_error(e)
            return None


class GuardDutyService(AWSService):
    def __init__(self, session):
        super().__init__(session)
        self.name = "guardduty"
        self.client = self.session.client("guardduty")

    def generate(self) -> Dict[str, Any]:
        try:
            guardduty_data = {"detectors": []}

            # List detectors
            detector_ids = self.client.list_detectors()["DetectorIds"]
            for detector_id in detector_ids:
                detector = self.client.get_detector(DetectorId=detector_id)

                # Get findings statistics
                stats = self.client.get_findings_statistics(
                    DetectorId=detector_id, FindingStatisticTypes=["COUNT_BY_SEVERITY"]
                )

                # Get filter information
                try:
                    filters = self.client.list_filters(DetectorId=detector_id)[
                        "FilterNames"
                    ]
                    filter_details = []
                    for filter_name in filters:
                        filter_data = self.client.get_filter(
                            DetectorId=detector_id, FilterName=filter_name
                        )
                        filter_details.append(filter_data)
                except ClientError:
                    filter_details = []

                # Get IP set information
                try:
                    ip_sets = self.client.list_ip_sets(DetectorId=detector_id)[
                        "IpSetIds"
                    ]
                    ip_set_details = []
                    for ip_set_id in ip_sets:
                        ip_set = self.client.get_ip_set(
                            DetectorId=detector_id, IpSetId=ip_set_id
                        )
                        ip_set_details.append(ip_set)
                except ClientError:
                    ip_set_details = []

                # Get threat intel set information
                try:
                    threat_intel_sets = self.client.list_threat_intel_sets(
                        DetectorId=detector_id
                    )["ThreatIntelSetIds"]
                    threat_intel_details = []
                    for threat_set_id in threat_intel_sets:
                        threat_set = self.client.get_threat_intel_set(
                            DetectorId=detector_id, ThreatIntelSetId=threat_set_id
                        )
                        threat_intel_details.append(threat_set)
                except ClientError:
                    threat_intel_details = []

                # Get publishing destination information
                try:
                    destinations = self.client.list_publishing_destinations(
                        DetectorId=detector_id
                    )["Destinations"]
                    destination_details = []
                    for dest in destinations:
                        destination = self.client.describe_publishing_destination(
                            DetectorId=detector_id, DestinationId=dest["DestinationId"]
                        )
                        destination_details.append(destination)
                except ClientError:
                    destination_details = []

                detector_data = {
                    "id": detector_id,
                    "status": detector.get("Status"),
                    "service_role": detector.get("ServiceRole"),
                    "data_sources": detector.get("DataSources", {}),
                    "features": detector.get("Features", []),
                    "finding_statistics": stats.get("FindingStatistics", {}),
                    "filters": filter_details,
                    "ip_sets": ip_set_details,
                    "threat_intel_sets": threat_intel_details,
                    "publishing_destinations": destination_details,
                    "tags": self.client.list_tags_for_resource(
                        ResourceArn=f"arn:aws:guardduty:{self.session.region_name}:{self.session.client('sts').get_caller_identity()['Account']}:detector/{detector_id}"
                    ).get("Tags", {}),
                }
                guardduty_data["detectors"].append(detector_data)

            return guardduty_data

        except ClientError as e:
            self.handle_error(e)
            return None


class OpenSearchService(AWSService):
    def __init__(self, session):
        super().__init__(session)
        self.name = "opensearch"
        self.client = self.session.client("opensearch")

    def generate(self) -> Dict[str, Any]:
        try:
            opensearch_data = {"domains": []}

            # List domains
            domain_names = self.client.list_domain_names()["DomainNames"]
            for domain in domain_names:
                domain_name = domain["DomainName"]

                # Get domain configuration
                domain_config = self.client.describe_domain(DomainName=domain_name)[
                    "DomainStatus"
                ]

                # Get domain configuration options
                config_options = self.client.describe_domain_config(
                    DomainName=domain_name
                )["DomainConfig"]

                # Get VPC endpoints if available
                try:
                    vpc_endpoints = self.client.describe_vpc_endpoints(
                        DomainName=domain_name
                    )["VpcEndpoints"]
                except ClientError:
                    vpc_endpoints = []

                # Get packages if available
                try:
                    packages = self.client.list_packages_for_domain(
                        DomainName=domain_name
                    )["DomainPackageDetails"]
                except ClientError:
                    packages = []

                domain_data = {
                    "name": domain_name,
                    "arn": domain_config["ARN"],
                    "engine_version": domain_config.get("EngineVersion"),
                    "cluster_config": domain_config.get("ClusterConfig", {}),
                    "ebs_options": domain_config.get("EBSOptions", {}),
                    "access_policies": domain_config.get("AccessPolicies"),
                    "snapshot_options": domain_config.get("SnapshotOptions", {}),
                    "vpc_options": domain_config.get("VPCOptions", {}),
                    "cognito_options": domain_config.get("CognitoOptions", {}),
                    "encryption_at_rest": domain_config.get(
                        "EncryptionAtRestOptions", {}
                    ),
                    "node_to_node_encryption": domain_config.get(
                        "NodeToNodeEncryptionOptions", {}
                    ),
                    "advanced_options": domain_config.get("AdvancedOptions", {}),
                    "service_software_options": domain_config.get(
                        "ServiceSoftwareOptions", {}
                    ),
                    "domain_endpoint_options": domain_config.get(
                        "DomainEndpointOptions", {}
                    ),
                    "advanced_security_options": domain_config.get(
                        "AdvancedSecurityOptions", {}
                    ),
                    "auto_tune_options": domain_config.get("AutoTuneOptions", {}),
                    "change_progress_details": domain_config.get(
                        "ChangeProgressDetails", {}
                    ),
                    "configuration_options": config_options,
                    "vpc_endpoints": vpc_endpoints,
                    "packages": packages,
                    "tags": self.client.list_tags(ARN=domain_config["ARN"]).get(
                        "TagList", []
                    ),
                }
                opensearch_data["domains"].append(domain_data)

            return opensearch_data

        except ClientError as e:
            self.handle_error(e)
            return None


class SecretsManagerService(AWSService):
    def __init__(self, session):
        super().__init__(session)
        self.name = "secretsmanager"
        self.client = self.session.client("secretsmanager")

    def generate(self) -> Dict[str, Any]:
        try:
            secrets_data = {"secrets": []}

            # List secrets
            paginator = self.client.get_paginator("list_secrets")
            for page in paginator.paginate():
                for secret in page["SecretList"]:
                    # Get policy if available
                    try:
                        policy = self.client.get_resource_policy(
                            SecretId=secret["ARN"]
                        ).get("ResourcePolicy")
                    except ClientError:
                        policy = None

                    # Get rotation configuration if enabled
                    rotation_config = {}
                    if secret.get("RotationEnabled"):
                        try:
                            rotation = self.client.describe_secret(
                                SecretId=secret["ARN"]
                            )
                            rotation_config = {
                                "rotation_enabled": rotation.get("RotationEnabled"),
                                "rotation_lambda_arn": rotation.get(
                                    "RotationLambdaARN"
                                ),
                                "rotation_rules": rotation.get("RotationRules", {}),
                                "last_rotated_date": str(
                                    rotation.get("LastRotatedDate", "")
                                ),
                            }
                        except ClientError:
                            pass

                    secret_data = {
                        "name": secret["Name"],
                        "arn": secret["ARN"],
                        "description": secret.get("Description"),
                        "kms_key_id": secret.get("KmsKeyId"),
                        "rotation_enabled": secret.get("RotationEnabled", False),
                        "last_changed_date": str(secret.get("LastChangedDate", "")),
                        "last_accessed_date": str(secret.get("LastAccessedDate", "")),
                        "deleted_date": str(secret.get("DeletedDate", "")),
                        "tags": secret.get("Tags", []),
                        "secret_versions_to_stages": secret.get(
                            "SecretVersionsToStages", {}
                        ),
                        "owning_service": secret.get("OwningService"),
                        "policy": policy,
                        "rotation_configuration": rotation_config,
                    }
                    secrets_data["secrets"].append(secret_data)

            return secrets_data

        except ClientError as e:
            self.handle_error(e)
            return None


class SecurityHubService(AWSService):
    def __init__(self, session):
        super().__init__(session)
        self.name = "securityhub"
        self.client = self.session.client("securityhub")

    def generate(self) -> Dict[str, Any]:
        try:
            securityhub_data = {
                "hub_configuration": {},
                "enabled_standards": [],
                "custom_actions": [],
                "finding_aggregators": [],
                "insight_results": [],
            }

            # Get hub configuration
            try:
                hub_config = self.client.describe_hub()
                securityhub_data["hub_configuration"] = {
                    "hub_arn": hub_config.get("HubArn"),
                    "subscribed_at": str(hub_config.get("SubscribedAt", "")),
                    "auto_enable_controls": hub_config.get("AutoEnableControls"),
                    "tags": hub_config.get("Tags", {}),
                }
            except ClientError:
                pass

            # Get enabled standards
            try:
                standards = self.client.get_enabled_standards()[
                    "StandardsSubscriptions"
                ]
                securityhub_data["enabled_standards"] = [
                    {
                        "standards_arn": std["StandardsArn"],
                        "standards_subscription_arn": std["StandardsSubscriptionArn"],
                        "standards_input": std.get("StandardsInput", {}),
                        "status": std.get("StandardsStatus"),
                        "status_reason": std.get("StandardsStatusReason", {}),
                    }
                    for std in standards
                ]
            except ClientError:
                pass

            # Get custom actions
            try:
                actions = self.client.describe_action_targets()["ActionTargets"]
                securityhub_data["custom_actions"] = [
                    {
                        "action_target_arn": action["ActionTargetArn"],
                        "name": action["Name"],
                        "description": action.get("Description"),
                    }
                    for action in actions
                ]
            except ClientError:
                pass

            # Get finding aggregators
            try:
                aggregators = self.client.list_finding_aggregators()[
                    "FindingAggregators"
                ]
                for agg in aggregators:
                    agg_details = self.client.describe_finding_aggregator(
                        FindingAggregatorArn=agg["FindingAggregatorArn"]
                    )
                    securityhub_data["finding_aggregators"].append(
                        {
                            "arn": agg_details["FindingAggregatorArn"],
                            "region_linking_mode": agg_details.get("RegionLinkingMode"),
                            "regions": agg_details.get("Regions", []),
                        }
                    )
            except ClientError:
                pass

            # Get insight results
            try:
                insights = self.client.get_insights()["Insights"]
                for insight in insights:
                    try:
                        result = self.client.get_insight_results(
                            InsightArn=insight["InsightArn"]
                        )["InsightResults"]
                        securityhub_data["insight_results"].append(
                            {
                                "insight_arn": insight["InsightArn"],
                                "name": insight["Name"],
                                "filters": insight.get("Filters", {}),
                                "group_by_attribute": insight.get("GroupByAttribute"),
                                "results": result,
                            }
                        )
                    except ClientError:
                        continue
            except ClientError:
                pass

            return securityhub_data

        except ClientError as e:
            self.handle_error(e)
            return None


class WAFv2Service(AWSService):
    def __init__(self, session):
        super().__init__(session)
        self.name = "wafv2"
        self.client = self.session.client("wafv2")

    def _get_web_acl_details(
        self, web_acl: Dict[str, Any], scope: str
    ) -> Dict[str, Any]:
        """Get detailed information about a web ACL."""
        try:
            acl_details = self.client.get_web_acl(
                Name=web_acl["Name"], Scope=scope, Id=web_acl["Id"]
            )["WebACL"]

            # Get logging configuration if available
            try:
                logging_config = self.client.get_logging_configuration(
                    ResourceArn=acl_details["ARN"]
                )["LoggingConfiguration"]
            except ClientError:
                logging_config = {}

            return {
                "name": acl_details["Name"],
                "id": acl_details["Id"],
                "arn": acl_details["ARN"],
                "description": acl_details.get("Description"),
                "default_action": acl_details.get("DefaultAction", {}),
                "rules": acl_details.get("Rules", []),
                "visibility_config": acl_details.get("VisibilityConfig", {}),
                "capacity": acl_details.get("Capacity"),
                "logging_configuration": logging_config,
                "labels": acl_details.get("LabelNamespace", []),
                "custom_response_bodies": acl_details.get("CustomResponseBodies", {}),
                "captcha_config": acl_details.get("CaptchaConfig", {}),
                "challenge_config": acl_details.get("ChallengeConfig", {}),
                "tags": self.client.list_tags_for_resource(
                    ResourceARN=acl_details["ARN"]
                )
                .get("TagInfoForResource", {})
                .get("TagList", []),
            }
        except ClientError:
            return {}

    def _get_rule_group_details(
        self, rule_group: Dict[str, Any], scope: str
    ) -> Dict[str, Any]:
        """Get detailed information about a rule group."""
        try:
            group_details = self.client.get_rule_group(
                Name=rule_group["Name"], Scope=scope, Id=rule_group["Id"]
            )["RuleGroup"]

            return {
                "name": group_details["Name"],
                "id": group_details["Id"],
                "arn": group_details["ARN"],
                "description": group_details.get("Description"),
                "capacity": group_details.get("Capacity"),
                "rules": group_details.get("Rules", []),
                "visibility_config": group_details.get("VisibilityConfig", {}),
                "labels": group_details.get("LabelNamespace", []),
                "custom_response_bodies": group_details.get("CustomResponseBodies", {}),
                "available_labels": group_details.get("AvailableLabels", []),
                "consumed_labels": group_details.get("ConsumedLabels", []),
                "tags": self.client.list_tags_for_resource(
                    ResourceARN=group_details["ARN"]
                )
                .get("TagInfoForResource", {})
                .get("TagList", []),
            }
        except ClientError:
            return {}

    def generate(self) -> Dict[str, Any]:
        try:
            wafv2_data = {
                "web_acls": {"regional": [], "cloudfront": []},
                "rule_groups": {"regional": [], "cloudfront": []},
                "ip_sets": {"regional": [], "cloudfront": []},
                "regex_pattern_sets": {"regional": [], "cloudfront": []},
            }

            # Process both REGIONAL and CLOUDFRONT scopes
            for scope in ["REGIONAL", "CLOUDFRONT"]:
                scope_key = scope.lower()

                # Get Web ACLs
                try:
                    web_acls = self.client.list_web_acls(Scope=scope)["WebACLs"]
                    for acl in web_acls:
                        acl_details = self._get_web_acl_details(acl, scope)
                        if acl_details:
                            wafv2_data["web_acls"][scope_key].append(acl_details)
                except ClientError:
                    pass

                # Get Rule Groups
                try:
                    rule_groups = self.client.list_rule_groups(Scope=scope)[
                        "RuleGroups"
                    ]
                    for group in rule_groups:
                        group_details = self._get_rule_group_details(group, scope)
                        if group_details:
                            wafv2_data["rule_groups"][scope_key].append(group_details)
                except ClientError:
                    pass

                # Get IP Sets
                try:
                    ip_sets = self.client.list_ip_sets(Scope=scope)["IPSets"]
                    for ip_set in ip_sets:
                        try:
                            ip_set_details = self.client.get_ip_set(
                                Name=ip_set["Name"], Scope=scope, Id=ip_set["Id"]
                            )["IPSet"]
                            ip_set_data = {
                                "name": ip_set_details["Name"],
                                "id": ip_set_details["Id"],
                                "arn": ip_set_details["ARN"],
                                "description": ip_set_details.get("Description"),
                                "ip_address_version": ip_set_details.get(
                                    "IPAddressVersion"
                                ),
                                "addresses": ip_set_details.get("Addresses", []),
                                "tags": self.client.list_tags_for_resource(
                                    ResourceARN=ip_set_details["ARN"]
                                )
                                .get("TagInfoForResource", {})
                                .get("TagList", []),
                            }
                            wafv2_data["ip_sets"][scope_key].append(ip_set_data)
                        except ClientError:
                            continue
                except ClientError:
                    pass

                # Get Regex Pattern Sets
                try:
                    regex_sets = self.client.list_regex_pattern_sets(Scope=scope)[
                        "RegexPatternSets"
                    ]
                    for regex_set in regex_sets:
                        try:
                            regex_set_details = self.client.get_regex_pattern_set(
                                Name=regex_set["Name"], Scope=scope, Id=regex_set["Id"]
                            )["RegexPatternSet"]
                            regex_set_data = {
                                "name": regex_set_details["Name"],
                                "id": regex_set_details["Id"],
                                "arn": regex_set_details["ARN"],
                                "description": regex_set_details.get("Description"),
                                "regular_expressions": regex_set_details.get(
                                    "RegularExpressionList", []
                                ),
                                "tags": self.client.list_tags_for_resource(
                                    ResourceARN=regex_set_details["ARN"]
                                )
                                .get("TagInfoForResource", {})
                                .get("TagList", []),
                            }
                            wafv2_data["regex_pattern_sets"][scope_key].append(
                                regex_set_data
                            )
                        except ClientError:
                            continue
                except ClientError:
                    pass

            return wafv2_data

        except ClientError as e:
            self.handle_error(e)
            return None


class CloudFrontService(AWSService):
    def __init__(self, session):
        super().__init__(session)
        self.name = "cloudfront"
        self.client = self.session.client("cloudfront")

    def generate(self) -> Dict[str, Any]:
        try:
            cloudfront_data = {
                "distributions": [],
                "functions": [],
                "cache_policies": [],
                "origin_request_policies": [],
                "response_headers_policies": [],
                "key_groups": [],
            }

            # List distributions
            try:
                paginator = self.client.get_paginator("list_distributions")
                for page in paginator.paginate():
                    if "Items" in page.get("DistributionList", {}):
                        for dist in page["DistributionList"]["Items"]:
                            # Get detailed configuration
                            dist_config = self.client.get_distribution(Id=dist["Id"])[
                                "Distribution"
                            ]

                            # Get tags
                            try:
                                tags = (
                                    self.client.list_tags_for_resource(
                                        Resource=dist["ARN"]
                                    )
                                    .get("Tags", {})
                                    .get("Items", [])
                                )
                            except ClientError:
                                tags = []

                            dist_data = {
                                "id": dist["Id"],
                                "arn": dist["ARN"],
                                "domain_name": dist.get("DomainName"),
                                "status": dist.get("Status"),
                                "last_modified_time": str(
                                    dist.get("LastModifiedTime", "")
                                ),
                                "in_progress_invalidation_batches": dist.get(
                                    "InProgressInvalidationBatches", 0
                                ),
                                "aliases": dist.get("Aliases", {}),
                                "origins": dist_config.get(
                                    "DistributionConfig", {}
                                ).get("Origins", {}),
                                "default_cache_behavior": dist_config.get(
                                    "DistributionConfig", {}
                                ).get("DefaultCacheBehavior", {}),
                                "cache_behaviors": dist_config.get(
                                    "DistributionConfig", {}
                                ).get("CacheBehaviors", {}),
                                "custom_error_responses": dist_config.get(
                                    "DistributionConfig", {}
                                ).get("CustomErrorResponses", {}),
                                "comment": dist_config.get(
                                    "DistributionConfig", {}
                                ).get("Comment"),
                                "logging": dist_config.get(
                                    "DistributionConfig", {}
                                ).get("Logging", {}),
                                "price_class": dist_config.get(
                                    "DistributionConfig", {}
                                ).get("PriceClass"),
                                "enabled": dist_config.get(
                                    "DistributionConfig", {}
                                ).get("Enabled"),
                                "viewer_certificate": dist_config.get(
                                    "DistributionConfig", {}
                                ).get("ViewerCertificate", {}),
                                "restrictions": dist_config.get(
                                    "DistributionConfig", {}
                                ).get("Restrictions", {}),
                                "web_acl_id": dist_config.get(
                                    "DistributionConfig", {}
                                ).get("WebACLId"),
                                "http_version": dist_config.get(
                                    "DistributionConfig", {}
                                ).get("HttpVersion"),
                                "is_ipv6_enabled": dist_config.get(
                                    "DistributionConfig", {}
                                ).get("IsIPV6Enabled"),
                                "tags": tags,
                            }
                            cloudfront_data["distributions"].append(dist_data)
            except ClientError:
                pass

            # List functions
            try:
                functions = self.client.list_functions()
                if "FunctionList" in functions and "Items" in functions["FunctionList"]:
                    for func in functions["FunctionList"]["Items"]:
                        try:
                            # Get function details with DEVELOPMENT stage first
                            try:
                                func_details = self.client.describe_function(
                                    Name=func["Name"], Stage="DEVELOPMENT"
                                )["Function"]
                            except ClientError:
                                # If DEVELOPMENT stage fails, try LIVE stage
                                func_details = self.client.describe_function(
                                    Name=func["Name"], Stage="LIVE"
                                )["Function"]

                            func_data = {
                                "name": func_details["Name"],
                                "status": func_details.get("Status"),
                                "runtime": func_details.get("FunctionConfig", {}).get(
                                    "Runtime"
                                ),
                                "arn": func_details.get("FunctionMetadata", {}).get(
                                    "FunctionARN"
                                ),
                                "stage": func_details.get("FunctionMetadata", {}).get(
                                    "Stage"
                                ),
                                "created_time": str(
                                    func_details.get("FunctionMetadata", {}).get(
                                        "CreatedTime", ""
                                    )
                                ),
                                "last_modified_time": str(
                                    func_details.get("FunctionMetadata", {}).get(
                                        "LastModifiedTime", ""
                                    )
                                ),
                            }
                            cloudfront_data["functions"].append(func_data)
                        except ClientError:
                            # Skip this function if we can't get details for either stage
                            continue
            except ClientError:
                pass

            # List cache policies
            try:
                cache_policies = self.client.list_cache_policies()
                if (
                    "CachePolicyList" in cache_policies
                    and "Items" in cache_policies["CachePolicyList"]
                ):
                    for policy in cache_policies["CachePolicyList"]["Items"]:
                        policy_details = self.client.get_cache_policy(
                            Id=policy["CachePolicy"]["Id"]
                        )["CachePolicy"]
                        cloudfront_data["cache_policies"].append(policy_details)
            except ClientError:
                pass

            # List origin request policies
            try:
                origin_policies = self.client.list_origin_request_policies()
                if (
                    "OriginRequestPolicyList" in origin_policies
                    and "Items" in origin_policies["OriginRequestPolicyList"]
                ):
                    for policy in origin_policies["OriginRequestPolicyList"]["Items"]:
                        policy_details = self.client.get_origin_request_policy(
                            Id=policy["OriginRequestPolicy"]["Id"]
                        )["OriginRequestPolicy"]
                        cloudfront_data["origin_request_policies"].append(
                            policy_details
                        )
            except ClientError:
                pass

            # List response headers policies
            try:
                header_policies = self.client.list_response_headers_policies()
                if (
                    "ResponseHeadersPolicyList" in header_policies
                    and "Items" in header_policies["ResponseHeadersPolicyList"]
                ):
                    for policy in header_policies["ResponseHeadersPolicyList"]["Items"]:
                        policy_details = self.client.get_response_headers_policy(
                            Id=policy["ResponseHeadersPolicy"]["Id"]
                        )["ResponseHeadersPolicy"]
                        cloudfront_data["response_headers_policies"].append(
                            policy_details
                        )
            except ClientError:
                pass

            # List key groups
            try:
                key_groups = self.client.list_key_groups()
                if (
                    "KeyGroupList" in key_groups
                    and "Items" in key_groups["KeyGroupList"]
                ):
                    for group in key_groups["KeyGroupList"]["Items"]:
                        group_details = self.client.get_key_group(
                            Id=group["KeyGroup"]["Id"]
                        )["KeyGroup"]
                        cloudfront_data["key_groups"].append(group_details)
            except ClientError:
                pass

            return cloudfront_data

        except ClientError as e:
            self.handle_error(e)
            return None


class AccessAnalyzerService(AWSService):
    def __init__(self, session):
        super().__init__(session)
        self.name = "accessanalyzer"
        self.client = self.session.client("accessanalyzer")

    def generate(self) -> Dict[str, Any]:
        try:
            analyzer_data = {"analyzers": [], "findings": []}

            # List analyzers
            try:
                paginator = self.client.get_paginator("list_analyzers")
                for page in paginator.paginate():
                    for analyzer in page.get("analyzers", []):
                        analyzer_info = {
                            "name": analyzer["name"],
                            "arn": analyzer["arn"],
                            "type": analyzer.get("type"),
                            "status": analyzer.get("status"),
                            "last_resource_analyzed": analyzer.get(
                                "lastResourceAnalyzed"
                            ),
                            "last_resource_analyzed_at": str(
                                analyzer.get("lastResourceAnalyzedAt", "")
                            ),
                            "tags": analyzer.get("tags", {}),
                        }

                        # Get findings for this analyzer
                        try:
                            findings_paginator = self.client.get_paginator(
                                "list_findings"
                            )
                            for findings_page in findings_paginator.paginate(
                                analyzerArn=analyzer["arn"]
                            ):
                                for finding in findings_page.get("findings", []):
                                    finding_info = {
                                        "id": finding["id"],
                                        "analyzer_arn": finding["analyzerArn"],
                                        "resource_type": finding.get("resourceType"),
                                        "resource": finding.get("resource"),
                                        "status": finding.get("status"),
                                        "created_at": str(finding.get("createdAt", "")),
                                        "updated_at": str(finding.get("updatedAt", "")),
                                        "analyzed_at": str(
                                            finding.get("analyzedAt", "")
                                        ),
                                    }
                                    analyzer_data["findings"].append(finding_info)
                        except ClientError:
                            pass

                        analyzer_data["analyzers"].append(analyzer_info)
            except ClientError:
                pass

            return analyzer_data

        except ClientError as e:
            self.handle_error(e)
            return None


class AutoScalingService(AWSService):
    def __init__(self, session):
        super().__init__(session)
        self.name = "autoscaling"
        self.client = self.session.client("autoscaling")

    def generate(self) -> Dict[str, Any]:
        try:
            autoscaling_data = {
                "groups": [],
                "launch_configurations": [],
                "scaling_policies": [],
            }

            # List Auto Scaling groups
            try:
                paginator = self.client.get_paginator("describe_auto_scaling_groups")
                for page in paginator.paginate():
                    for group in page.get("AutoScalingGroups", []):
                        group_info = {
                            "name": group["AutoScalingGroupName"],
                            "arn": group["AutoScalingGroupARN"],
                            "launch_configuration": group.get(
                                "LaunchConfigurationName"
                            ),
                            "launch_template": group.get("LaunchTemplate"),
                            "min_size": group.get("MinSize"),
                            "max_size": group.get("MaxSize"),
                            "desired_capacity": group.get("DesiredCapacity"),
                            "default_cooldown": group.get("DefaultCooldown"),
                            "availability_zones": group.get("AvailabilityZones", []),
                            "load_balancer_names": group.get("LoadBalancerNames", []),
                            "target_group_arns": group.get("TargetGroupARNs", []),
                            "health_check_type": group.get("HealthCheckType"),
                            "health_check_grace_period": group.get(
                                "HealthCheckGracePeriod"
                            ),
                            "instances": [
                                {
                                    "id": instance["InstanceId"],
                                    "health_status": instance.get("HealthStatus"),
                                    "lifecycle_state": instance.get("LifecycleState"),
                                    "availability_zone": instance.get(
                                        "AvailabilityZone"
                                    ),
                                }
                                for instance in group.get("Instances", [])
                            ],
                            "tags": group.get("Tags", []),
                        }
                        autoscaling_data["groups"].append(group_info)

                        # Get scaling policies for this group
                        try:
                            policies_paginator = self.client.get_paginator(
                                "describe_policies"
                            )
                            for policies_page in policies_paginator.paginate(
                                AutoScalingGroupName=group["AutoScalingGroupName"]
                            ):
                                for policy in policies_page.get("ScalingPolicies", []):
                                    policy_info = {
                                        "name": policy["PolicyName"],
                                        "arn": policy["PolicyARN"],
                                        "group_name": policy["AutoScalingGroupName"],
                                        "policy_type": policy.get("PolicyType"),
                                        "adjustment_type": policy.get("AdjustmentType"),
                                        "min_adjustment_step": policy.get(
                                            "MinAdjustmentStep"
                                        ),
                                        "min_adjustment_magnitude": policy.get(
                                            "MinAdjustmentMagnitude"
                                        ),
                                        "scaling_adjustment": policy.get(
                                            "ScalingAdjustment"
                                        ),
                                        "cooldown": policy.get("Cooldown"),
                                        "metric_aggregation_type": policy.get(
                                            "MetricAggregationType"
                                        ),
                                        "target_tracking_configuration": policy.get(
                                            "TargetTrackingConfiguration"
                                        ),
                                        "enabled": policy.get("Enabled", True),
                                    }
                                    autoscaling_data["scaling_policies"].append(
                                        policy_info
                                    )
                        except ClientError:
                            pass
            except ClientError:
                pass

            # List Launch Configurations
            try:
                paginator = self.client.get_paginator("describe_launch_configurations")
                for page in paginator.paginate():
                    for config in page.get("LaunchConfigurations", []):
                        config_info = {
                            "name": config["LaunchConfigurationName"],
                            "arn": config["LaunchConfigurationARN"],
                            "image_id": config.get("ImageId"),
                            "instance_type": config.get("InstanceType"),
                            "security_groups": config.get("SecurityGroups", []),
                            "key_name": config.get("KeyName"),
                            "user_data": config.get("UserData"),
                            "iam_instance_profile": config.get("IamInstanceProfile"),
                            "ebs_optimized": config.get("EbsOptimized", False),
                            "spot_price": config.get("SpotPrice"),
                            "instance_monitoring": config.get(
                                "InstanceMonitoring", {}
                            ).get("Enabled", False),
                            "created_time": str(config.get("CreatedTime", "")),
                        }
                        autoscaling_data["launch_configurations"].append(config_info)
            except ClientError:
                pass

            return autoscaling_data

        except ClientError as e:
            self.handle_error(e)
            return None


class BackupService(AWSService):
    def __init__(self, session):
        super().__init__(session)
        self.name = "backup"
        self.client = self.session.client("backup")

    def generate(self) -> Dict[str, Any]:
        try:
            backup_data = {"vaults": [], "plans": [], "selections": [], "jobs": []}

            # List backup vaults
            try:
                paginator = self.client.get_paginator("list_backup_vaults")
                for page in paginator.paginate():
                    for vault in page.get("BackupVaultList", []):
                        vault_info = {
                            "name": vault["BackupVaultName"],
                            "arn": vault["BackupVaultArn"],
                            "creation_date": str(vault.get("CreationDate", "")),
                            "encryption_key_arn": vault.get("EncryptionKeyArn"),
                            "creator_request_id": vault.get("CreatorRequestId"),
                            "number_of_recovery_points": vault.get(
                                "NumberOfRecoveryPoints"
                            ),
                            "locked": vault.get("Locked", False),
                            "min_retention_days": vault.get("MinRetentionDays"),
                            "max_retention_days": vault.get("MaxRetentionDays"),
                            "tags": self.client.list_tags(
                                ResourceArn=vault["BackupVaultArn"]
                            ).get("Tags", {}),
                        }
                        backup_data["vaults"].append(vault_info)
            except ClientError:
                pass

            # List backup plans
            try:
                paginator = self.client.get_paginator("list_backup_plans")
                for page in paginator.paginate():
                    for plan in page.get("BackupPlansList", []):
                        plan_details = self.client.get_backup_plan(
                            BackupPlanId=plan["BackupPlanId"]
                        )["BackupPlan"]

                        plan_info = {
                            "id": plan["BackupPlanId"],
                            "arn": plan["BackupPlanArn"],
                            "name": plan["BackupPlanName"],
                            "version_id": plan.get("VersionId"),
                            "creation_date": str(plan.get("CreationDate", "")),
                            "last_execution_date": str(
                                plan.get("LastExecutionDate", "")
                            ),
                            "rules": plan_details.get("Rules", []),
                            "advanced_backup_settings": plan_details.get(
                                "AdvancedBackupSettings", []
                            ),
                            "tags": self.client.list_tags(
                                ResourceArn=plan["BackupPlanArn"]
                            ).get("Tags", {}),
                        }
                        backup_data["plans"].append(plan_info)

                        # Get selections for this plan
                        try:
                            selections_paginator = self.client.get_paginator(
                                "list_backup_selections"
                            )
                            for selections_page in selections_paginator.paginate(
                                BackupPlanId=plan["BackupPlanId"]
                            ):
                                for selection in selections_page.get(
                                    "BackupSelectionsList", []
                                ):
                                    selection_details = (
                                        self.client.get_backup_selection(
                                            BackupPlanId=plan["BackupPlanId"],
                                            SelectionId=selection["SelectionId"],
                                        )["BackupSelection"]
                                    )

                                    selection_info = {
                                        "id": selection["SelectionId"],
                                        "name": selection_details.get("SelectionName"),
                                        "iam_role_arn": selection_details.get(
                                            "IamRoleArn"
                                        ),
                                        "resources": selection_details.get(
                                            "Resources", []
                                        ),
                                        "list_of_tags": selection_details.get(
                                            "ListOfTags", []
                                        ),
                                        "conditions": selection_details.get(
                                            "Conditions", {}
                                        ),
                                    }
                                    backup_data["selections"].append(selection_info)
                        except ClientError:
                            pass
            except ClientError:
                pass

            # List backup jobs from last 30 days
            try:
                paginator = self.client.get_paginator("list_backup_jobs")
                for page in paginator.paginate():
                    for job in page.get("BackupJobs", []):
                        job_info = {
                            "job_id": job["BackupJobId"],
                            "vault_name": job.get("BackupVaultName"),
                            "creation_date": str(job.get("CreationDate", "")),
                            "completion_date": str(job.get("CompletionDate", "")),
                            "state": job.get("State"),
                            "status_message": job.get("StatusMessage"),
                            "resource_type": job.get("ResourceType"),
                            "resource_arn": job.get("ResourceArn"),
                            "backup_size_in_bytes": job.get("BackupSizeInBytes"),
                            "backup_type": job.get("BackupType"),
                            "percent_done": job.get("PercentDone"),
                        }
                        backup_data["jobs"].append(job_info)
            except ClientError:
                pass

            return backup_data

        except ClientError as e:
            self.handle_error(e)
            return None


class CloudWatchService(AWSService):
    def __init__(self, session):
        super().__init__(session)
        self.name = "cloudwatch"
        self.client = self.session.client("cloudwatch")
        self.logs_client = self.session.client("logs")

    def generate(self) -> Dict[str, Any]:
        try:
            cloudwatch_data = {
                "alarms": [],
                "dashboards": [],
                "log_groups": [],
                "metric_streams": [],
            }

            # List alarms
            try:
                alarms = self.client.describe_alarms()
                for alarm in alarms.get("MetricAlarms", []):
                    alarm_info = {
                        "name": alarm["AlarmName"],
                        "arn": alarm["AlarmArn"],
                        "description": alarm.get("AlarmDescription"),
                        "state": {
                            "value": alarm.get("StateValue"),
                            "reason": alarm.get("StateReason"),
                            "updated": str(alarm.get("StateUpdatedTimestamp", "")),
                        },
                        "metric": {
                            "namespace": alarm.get("Namespace"),
                            "name": alarm.get("MetricName"),
                            "dimensions": alarm.get("Dimensions", []),
                        },
                        "configuration": {
                            "period": alarm.get("Period"),
                            "evaluation_periods": alarm.get("EvaluationPeriods"),
                            "threshold": alarm.get("Threshold"),
                            "comparison_operator": alarm.get("ComparisonOperator"),
                            "statistic": alarm.get("Statistic"),
                            "treat_missing_data": alarm.get("TreatMissingData"),
                        },
                        "actions": {
                            "alarm": alarm.get("AlarmActions", []),
                            "ok": alarm.get("OKActions", []),
                            "insufficient_data": alarm.get(
                                "InsufficientDataActions", []
                            ),
                        },
                        "tags": self.client.list_tags_for_resource(
                            ResourceARN=alarm["AlarmArn"]
                        ).get("Tags", []),
                    }
                    cloudwatch_data["alarms"].append(alarm_info)
            except ClientError:
                pass

            # List dashboards
            try:
                dashboards = self.client.list_dashboards()
                for dashboard in dashboards.get("DashboardEntries", []):
                    try:
                        dashboard_details = self.client.get_dashboard(
                            DashboardName=dashboard["DashboardName"]
                        )
                        dashboard_info = {
                            "name": dashboard["DashboardName"],
                            "arn": dashboard["DashboardArn"],
                            "last_modified": str(dashboard.get("LastModified", "")),
                            "size": dashboard.get("Size"),
                            "body": dashboard_details.get("DashboardBody"),
                            "tags": self.client.list_tags_for_resource(
                                ResourceARN=dashboard["DashboardArn"]
                            ).get("Tags", []),
                        }
                        cloudwatch_data["dashboards"].append(dashboard_info)
                    except ClientError:
                        continue
            except ClientError:
                pass

            # List log groups
            try:
                log_groups = self.logs_client.describe_log_groups()
                for group in log_groups.get("logGroups", []):
                    group_info = {
                        "name": group["logGroupName"],
                        "arn": group.get("arn"),
                        "creation_time": str(group.get("creationTime", "")),
                        "retention_in_days": group.get("retentionInDays"),
                        "metric_filter_count": group.get("metricFilterCount"),
                        "stored_bytes": group.get("storedBytes"),
                        "kms_key_id": group.get("kmsKeyId"),
                        "tags": self.logs_client.list_tags_log_group(
                            logGroupName=group["logGroupName"]
                        ).get("tags", {}),
                    }
                    cloudwatch_data["log_groups"].append(group_info)
            except ClientError:
                pass

            # List metric streams
            try:
                streams = self.client.list_metric_streams()
                for stream in streams.get("Entries", []):
                    stream_info = {
                        "name": stream["Name"],
                        "arn": stream["Arn"],
                        "firehose_arn": stream.get("FirehoseArn"),
                        "role_arn": stream.get("RoleArn"),
                        "state": stream.get("State"),
                        "creation_date": str(stream.get("CreationDate", "")),
                        "last_update_date": str(stream.get("LastUpdateDate", "")),
                        "output_format": stream.get("OutputFormat"),
                        "tags": self.client.list_tags_for_resource(
                            ResourceARN=stream["Arn"]
                        ).get("Tags", []),
                    }
                    cloudwatch_data["metric_streams"].append(stream_info)
            except ClientError:
                pass

            return cloudwatch_data

        except ClientError as e:
            self.handle_error(e)
            return None


class ECRService(AWSService):
    def __init__(self, session):
        super().__init__(session)
        self.name = "ecr"
        self.client = self.session.client("ecr")

    def generate(self) -> Dict[str, Any]:
        try:
            ecr_data = {
                "repositories": [],
                "registry_policy": None,
                "registry_scanning_config": None,
                "registry_replication_config": None,
            }

            # Get registry-level configurations
            try:
                registry_policy = self.client.get_registry_policy()
                ecr_data["registry_policy"] = registry_policy.get("policyText")
            except ClientError:
                pass

            try:
                scanning_config = self.client.get_registry_scanning_configuration()
                ecr_data["registry_scanning_config"] = scanning_config.get(
                    "scanningConfiguration"
                )
            except ClientError:
                pass

            try:
                replication_config = self.client.describe_registry()
                ecr_data["registry_replication_config"] = replication_config.get(
                    "replicationConfiguration"
                )
            except ClientError:
                pass

            # List repositories
            try:
                paginator = self.client.get_paginator("describe_repositories")
                for page in paginator.paginate():
                    for repo in page.get("repositories", []):
                        repo_info = {
                            "name": repo["repositoryName"],
                            "arn": repo["repositoryArn"],
                            "uri": repo["repositoryUri"],
                            "created_at": str(repo.get("createdAt", "")),
                            "image_tag_mutability": repo.get("imageTagMutability"),
                            "encryption_configuration": repo.get(
                                "encryptionConfiguration", {}
                            ),
                            "image_scanning_configuration": repo.get(
                                "imageScanningConfiguration", {}
                            ),
                            "tags": self.client.list_tags_for_resource(
                                resourceArn=repo["repositoryArn"]
                            ).get("tags", []),
                        }

                        # Get repository policy
                        try:
                            policy = self.client.get_repository_policy(
                                repositoryName=repo["repositoryName"]
                            )
                            repo_info["policy"] = policy.get("policyText")
                        except ClientError:
                            repo_info["policy"] = None

                        # Get lifecycle policy
                        try:
                            lifecycle = self.client.get_lifecycle_policy(
                                repositoryName=repo["repositoryName"]
                            )
                            repo_info["lifecycle_policy"] = lifecycle.get(
                                "lifecyclePolicyText"
                            )
                        except ClientError:
                            repo_info["lifecycle_policy"] = None

                        # Get images (latest 100 only)
                        try:
                            images = []
                            image_paginator = self.client.get_paginator(
                                "describe_images"
                            )
                            for image_page in image_paginator.paginate(
                                repositoryName=repo["repositoryName"], maxResults=100
                            ):
                                for image in image_page.get("imageDetails", []):
                                    image_info = {
                                        "digest": image.get("imageDigest"),
                                        "tags": image.get("imageTags", []),
                                        "size_in_bytes": image.get("imageSizeInBytes"),
                                        "pushed_at": str(
                                            image.get("imagePushedAt", "")
                                        ),
                                        "scan_status": image.get("imageScanStatus", {}),
                                        "scan_findings": image.get(
                                            "imageScanFindingsSummary", {}
                                        ),
                                    }
                                    images.append(image_info)
                            repo_info["images"] = images
                        except ClientError:
                            repo_info["images"] = []

                        ecr_data["repositories"].append(repo_info)
            except ClientError:
                pass

            return ecr_data

        except ClientError as e:
            self.handle_error(e)
            return None


class EFSService(AWSService):
    def __init__(self, session):
        super().__init__(session)
        self.name = "efs"
        self.client = self.session.client("efs")

    def generate(self) -> Dict[str, Any]:
        try:
            efs_data = {"file_systems": [], "access_points": []}

            # List file systems
            try:
                paginator = self.client.get_paginator("describe_file_systems")
                for page in paginator.paginate():
                    for fs in page.get("FileSystems", []):
                        # Get mount targets for this file system
                        mount_targets = []
                        try:
                            mt_paginator = self.client.get_paginator(
                                "describe_mount_targets"
                            )
                            for mt_page in mt_paginator.paginate(
                                FileSystemId=fs["FileSystemId"]
                            ):
                                for mt in mt_page.get("MountTargets", []):
                                    # Get mount target security groups
                                    try:
                                        mt_security_groups = self.client.describe_mount_target_security_groups(
                                            MountTargetId=mt["MountTargetId"]
                                        )[
                                            "SecurityGroups"
                                        ]
                                    except ClientError:
                                        mt_security_groups = []

                                    mount_target = {
                                        "id": mt["MountTargetId"],
                                        "subnet_id": mt.get("SubnetId"),
                                        "availability_zone_id": mt.get(
                                            "AvailabilityZoneId"
                                        ),
                                        "availability_zone_name": mt.get(
                                            "AvailabilityZoneName"
                                        ),
                                        "ip_address": mt.get("IpAddress"),
                                        "network_interface_id": mt.get(
                                            "NetworkInterfaceId"
                                        ),
                                        "state": mt.get("LifeCycleState"),
                                        "security_groups": mt_security_groups,
                                    }
                                    mount_targets.append(mount_target)
                        except ClientError:
                            pass

                        # Get backup policy
                        try:
                            backup_policy = self.client.describe_backup_policy(
                                FileSystemId=fs["FileSystemId"]
                            )["BackupPolicy"]
                        except ClientError:
                            backup_policy = {}

                        # Get lifecycle configuration
                        try:
                            lifecycle = self.client.describe_lifecycle_configuration(
                                FileSystemId=fs["FileSystemId"]
                            )["LifecyclePolicies"]
                        except ClientError:
                            lifecycle = []

                        fs_info = {
                            "id": fs["FileSystemId"],
                            "arn": fs.get("FileSystemArn"),
                            "name": fs.get("Name"),
                            "size_in_bytes": fs.get("SizeInBytes", {}),
                            "creation_time": str(fs.get("CreationTime", "")),
                            "life_cycle_state": fs.get("LifeCycleState"),
                            "performance_mode": fs.get("PerformanceMode"),
                            "throughput_mode": fs.get("ThroughputMode"),
                            "provisioned_throughput": fs.get(
                                "ProvisionedThroughputInMibps"
                            ),
                            "encrypted": fs.get("Encrypted"),
                            "kms_key_id": fs.get("KmsKeyId"),
                            "availability_zone_id": fs.get("AvailabilityZoneId"),
                            "availability_zone_name": fs.get("AvailabilityZoneName"),
                            "mount_targets": mount_targets,
                            "backup_policy": backup_policy,
                            "lifecycle_policies": lifecycle,
                            "tags": self.client.list_tags_for_resource(
                                ResourceId=fs["FileSystemId"]
                            ).get("Tags", []),
                        }
                        efs_data["file_systems"].append(fs_info)
            except ClientError:
                pass

            # List access points
            try:
                paginator = self.client.get_paginator("describe_access_points")
                for page in paginator.paginate():
                    for ap in page.get("AccessPoints", []):
                        ap_info = {
                            "id": ap["AccessPointId"],
                            "arn": ap.get("AccessPointArn"),
                            "file_system_id": ap.get("FileSystemId"),
                            "name": ap.get("Name"),
                            "life_cycle_state": ap.get("LifeCycleState"),
                            "root_directory": ap.get("RootDirectory", {}),
                            "posix_user": ap.get("PosixUser", {}),
                            "client_token": ap.get("ClientToken"),
                            "tags": self.client.list_tags_for_resource(
                                ResourceId=ap["AccessPointId"]
                            ).get("Tags", []),
                        }
                        efs_data["access_points"].append(ap_info)
            except ClientError:
                pass

            return efs_data

        except ClientError as e:
            self.handle_error(e)
            return None


class OrganizationsService(AWSService):
    def __init__(self, session):
        super().__init__(session)
        self.name = "organizations"
        self.client = self.session.client("organizations")

    def generate(self) -> Dict[str, Any]:
        try:
            org_data = {
                "organization": {},
                "accounts": [],
                "organizational_units": [],
                "policies": {
                    "service_control": [],
                    "tag": [],
                    "backup": [],
                    "ai_services_opt_out": [],
                },
                "delegated_administrators": [],
            }

            # Describe organization
            try:
                org = self.client.describe_organization()["Organization"]
                org_data["organization"] = {
                    "id": org["Id"],
                    "arn": org["Arn"],
                    "feature_set": org.get("FeatureSet"),
                    "master_account_id": org.get("MasterAccountId"),
                    "master_account_email": org.get("MasterAccountEmail"),
                    "available_policy_types": org.get("AvailablePolicyTypes", []),
                }
            except ClientError:
                pass

            # List accounts
            try:
                paginator = self.client.get_paginator("list_accounts")
                for page in paginator.paginate():
                    for account in page.get("Accounts", []):
                        account_info = {
                            "id": account["Id"],
                            "arn": account["Arn"],
                            "email": account.get("Email"),
                            "name": account.get("Name"),
                            "status": account.get("Status"),
                            "joined_method": account.get("JoinedMethod"),
                            "joined_timestamp": str(account.get("JoinedTimestamp", "")),
                            "tags": self.client.list_tags_for_resource(
                                ResourceId=account["Id"]
                            ).get("Tags", []),
                        }
                        org_data["accounts"].append(account_info)
            except ClientError:
                pass

            # List organizational units
            try:
                roots = self.client.list_roots()["Roots"]
                for root in roots:
                    # Get OUs for this root
                    try:
                        paginator = self.client.get_paginator(
                            "list_organizational_units_for_parent"
                        )
                        for page in paginator.paginate(ParentId=root["Id"]):
                            for ou in page.get("OrganizationalUnits", []):
                                ou_info = {
                                    "id": ou["Id"],
                                    "arn": ou["Arn"],
                                    "name": ou.get("Name"),
                                    "tags": self.client.list_tags_for_resource(
                                        ResourceId=ou["Id"]
                                    ).get("Tags", []),
                                }
                                org_data["organizational_units"].append(ou_info)
                    except ClientError:
                        continue
            except ClientError:
                pass

            # List policies
            policy_types = {
                "SERVICE_CONTROL_POLICY": "service_control",
                "TAG_POLICY": "tag",
                "BACKUP_POLICY": "backup",
                "AISERVICES_OPT_OUT_POLICY": "ai_services_opt_out",
            }

            for policy_type, data_key in policy_types.items():
                try:
                    paginator = self.client.get_paginator("list_policies")
                    for page in paginator.paginate(Filter=policy_type):
                        for policy in page.get("Policies", []):
                            try:
                                policy_content = self.client.describe_policy(
                                    PolicyId=policy["Id"]
                                )["Policy"]
                                policy_info = {
                                    "id": policy["Id"],
                                    "arn": policy["Arn"],
                                    "name": policy.get("Name"),
                                    "description": policy.get("Description"),
                                    "type": policy.get("Type"),
                                    "aws_managed": policy.get("AwsManaged", False),
                                    "content": policy_content.get("Content"),
                                    "tags": self.client.list_tags_for_resource(
                                        ResourceId=policy["Id"]
                                    ).get("Tags", []),
                                }
                                org_data["policies"][data_key].append(policy_info)
                            except ClientError:
                                continue
                except ClientError:
                    continue

            # List delegated administrators
            try:
                paginator = self.client.get_paginator("list_delegated_administrators")
                for page in paginator.paginate():
                    for admin in page.get("DelegatedAdministrators", []):
                        admin_info = {
                            "id": admin["Id"],
                            "arn": admin["Arn"],
                            "email": admin.get("Email"),
                            "name": admin.get("Name"),
                            "status": admin.get("Status"),
                            "delegation_enabled_date": str(
                                admin.get("DelegationEnabledDate", "")
                            ),
                            "joined_timestamp": str(admin.get("JoinedTimestamp", "")),
                        }
                        org_data["delegated_administrators"].append(admin_info)
            except ClientError:
                pass

            return org_data

        except ClientError as e:
            self.handle_error(e)
            return None


class StepFunctionsService(AWSService):
    def __init__(self, session):
        super().__init__(session)
        self.name = "stepfunctions"
        self.client = self.session.client("stepfunctions")

    def generate(self) -> Dict[str, Any]:
        try:
            stepfunctions_data = {"state_machines": [], "executions": {}}

            # List state machines
            try:
                paginator = self.client.get_paginator("list_state_machines")
                for page in paginator.paginate():
                    for machine in page.get("stateMachines", []):
                        # Get state machine details
                        try:
                            machine_details = self.client.describe_state_machine(
                                stateMachineArn=machine["stateMachineArn"]
                            )

                            machine_info = {
                                "name": machine["name"],
                                "arn": machine["stateMachineArn"],
                                "type": machine_details.get("type"),
                                "creation_date": str(machine.get("creationDate", "")),
                                "role_arn": machine_details.get("roleArn"),
                                "definition": machine_details.get("definition"),
                                "logging_configuration": machine_details.get(
                                    "loggingConfiguration", {}
                                ),
                                "tracing_configuration": machine_details.get(
                                    "tracingConfiguration", {}
                                ),
                                "tags": self.client.list_tags_for_resource(
                                    resourceArn=machine["stateMachineArn"]
                                ).get("tags", {}),
                            }

                            # Get recent executions for this state machine
                            try:
                                executions = []
                                exec_paginator = self.client.get_paginator(
                                    "list_executions"
                                )
                                for exec_page in exec_paginator.paginate(
                                    stateMachineArn=machine["stateMachineArn"],
                                    maxResults=100,  # Limit to last 100 executions
                                ):
                                    for execution in exec_page.get("executions", []):
                                        try:
                                            execution_details = (
                                                self.client.describe_execution(
                                                    executionArn=execution[
                                                        "executionArn"
                                                    ]
                                                )
                                            )
                                            execution_info = {
                                                "name": execution.get("name"),
                                                "arn": execution["executionArn"],
                                                "status": execution.get("status"),
                                                "start_date": str(
                                                    execution.get("startDate", "")
                                                ),
                                                "stop_date": str(
                                                    execution.get("stopDate", "")
                                                ),
                                                "input": execution_details.get("input"),
                                                "output": execution_details.get(
                                                    "output"
                                                ),
                                                "error": execution_details.get("error"),
                                                "cause": execution_details.get("cause"),
                                                "trace_header": execution_details.get(
                                                    "traceHeader"
                                                ),
                                            }
                                            executions.append(execution_info)
                                        except ClientError:
                                            continue
                                stepfunctions_data["executions"][
                                    machine["name"]
                                ] = executions
                            except ClientError:
                                stepfunctions_data["executions"][machine["name"]] = []

                            stepfunctions_data["state_machines"].append(machine_info)
                        except ClientError:
                            continue
            except ClientError:
                pass

            return stepfunctions_data

        except ClientError as e:
            self.handle_error(e)
            return None


class TrustedAdvisorService(AWSService):
    def __init__(self, session):
        super().__init__(session)
        self.name = "trustedadvisor"
        self.client = self.session.client("support")

    def generate(self) -> Dict[str, Any]:
        try:
            advisor_data = {"checks": []}

            # List all available checks
            try:
                checks = self.client.describe_trusted_advisor_checks(language="en")[
                    "checks"
                ]

                for check in checks:
                    try:
                        # Get check results
                        result = self.client.describe_trusted_advisor_check_result(
                            checkId=check["id"], language="en"
                        )["result"]

                        # Get check summaries
                        summaries = (
                            self.client.describe_trusted_advisor_check_summaries(
                                checkIds=[check["id"]]
                            )["summaries"][0]
                        )

                        check_info = {
                            "id": check["id"],
                            "name": check["name"],
                            "description": check["description"],
                            "category": check["category"],
                            "metadata": check.get("metadata", []),
                            "result": {
                                "check_id": result.get("checkId"),
                                "timestamp": str(result.get("timestamp", "")),
                                "status": result.get("status"),
                                "resources_summary": result.get("resourcesSummary", {}),
                                "categories_summary": result.get(
                                    "categorySpecificSummary", {}
                                ),
                                "flagged_resources": result.get("flaggedResources", []),
                            },
                            "summaries": {
                                "has_flagged_resources": summaries.get(
                                    "hasFlaggedResources"
                                ),
                                "resources_summary": summaries.get(
                                    "resourcesSummary", {}
                                ),
                                "categories_summary": summaries.get(
                                    "categorySpecificSummary", {}
                                ),
                                "timestamp": str(summaries.get("timestamp", "")),
                            },
                        }

                        advisor_data["checks"].append(check_info)
                    except ClientError:
                        continue
            except ClientError:
                pass

            return advisor_data

        except ClientError as e:
            self.handle_error(e)
            return None


class AWSProvider:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

        # Get credentials from config, env vars, or instance profile
        self.aws_access_key = self.config.get("aws_access_key_id") or os.environ.get(
            "AWS_ACCESS_KEY_ID"
        )
        self.aws_secret_key = self.config.get(
            "aws_secret_access_key"
        ) or os.environ.get("AWS_SECRET_ACCESS_KEY")
        self.aws_session_token = self.config.get("aws_session_token") or os.environ.get(
            "AWS_SESSION_TOKEN"
        )

        # Get initial session for region discovery
        session_kwargs = {
            "region_name": "us-east-1"
        }  # Default region for initial session
        if self.aws_access_key and self.aws_secret_key:
            session_kwargs.update(
                {
                    "aws_access_key_id": self.aws_access_key,
                    "aws_secret_access_key": self.aws_secret_key,
                }
            )
            if (
                self.aws_session_token
                and self.aws_session_token != ""
                and self.aws_session_token != "aws_session_token"
            ):
                session_kwargs["aws_session_token"] = self.aws_session_token

        self.main_session = boto3.Session(**session_kwargs)
        self.client_session = None

        self.role_arn = self.config.get("role_arn") or os.environ.get("AWS_ROLE_ARN")
        if self.role_arn:
            kovr_arn = app_config[env]["role_arn"]
            self.kovr_session = self.assume_role(kovr_arn, self.main_session)
            self.client_session = self.assume_role(self.role_arn, self.kovr_session)
            credentials = self.client_session.get_credentials()
            self.aws_access_key = credentials.access_key
            self.aws_secret_key = credentials.secret_key
            self.aws_session_token = credentials.token

        self.initial_session = self.client_session or self.main_session

        # Get target regions
        self.target_regions = (
            [self.config.get("region")]
            if self.config.get("region")
            else self.get_active_regions()
        )

        logger.info(f"Will collect data from regions: {self.target_regions}")

        self.services = [
            EC2Service,
            IAMService,
            KMSService,
            S3Service,
            CloudTrailService,
            RDSService,
            VPCService,
            LambdaService,
            ECSService,
            SNSService,
            SQSService,
            ACMService,
            DynamoDBService,
            EKSService,
            ElastiCacheService,
            GuardDutyService,
            OpenSearchService,
            SecretsManagerService,
            SecurityHubService,
            WAFv2Service,
            # CloudFrontService,
            AccessAnalyzerService,
            AutoScalingService,
            BackupService,
            CloudWatchService,
            ECRService,
            EFSService,
            OrganizationsService,
            StepFunctionsService,
            TrustedAdvisorService,
        ]

    def assume_role(self, role_arn: str, session: boto3.Session) -> boto3.Session:
        sts_client = session.client("sts")
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

    def get_active_regions(self) -> List[str]:
        ec2 = self.initial_session.client("ec2", region_name="us-east-1")
        active_regions = []
        active_regions = [
            region["RegionName"]
            for region in ec2.describe_regions(AllRegions=False)["Regions"]
            if region["OptInStatus"] in ["opt-in-not-required", "opted-in"]
        ]
        return active_regions

    def get_session_for_region(self, region: str) -> boto3.Session:
        """Create a new session for the specified region."""
        session_kwargs = {"region_name": region}
        if self.aws_access_key and self.aws_secret_key:
            session_kwargs.update(
                {
                    "aws_access_key_id": self.aws_access_key,
                    "aws_secret_access_key": self.aws_secret_key,
                }
            )
            if self.aws_session_token:
                session_kwargs["aws_session_token"] = self.aws_session_token
        return boto3.Session(**session_kwargs)

    def get_account_id(self) -> str:
        """Get AWS Account ID."""
        sts = self.initial_session.client("sts")
        return sts.get_caller_identity()["Account"]

    def _is_empty_nested(self, data: Any) -> bool:
        """Check if all nested values in a dictionary are empty."""
        if isinstance(data, dict):
            return all(self._is_empty_nested(value) for value in data.values())
        elif isinstance(data, (list, tuple, set)):
            return len(data) == 0
        elif isinstance(data, str):
            return len(data.strip()) == 0
        elif data is None:
            return True
        return False

    def process_service(self, service_class, region: str) -> tuple:
        """Process a single service in a specific region and return its data."""
        session = self.get_session_for_region(region)
        service_instance = service_class(session)
        service_name = service_instance.name
        try:
            logger.debug(f"Starting collection for {service_name} in region {region}")
            data = service_instance.generate()
            if data and not self._is_empty_nested(data):
                logger.debug(
                    f"Successfully collected data for {service_name} in region {region}"
                )
                return service_name, data
            logger.debug(f"No data collected for {service_name} in region {region}")
            return service_name, None
        except Exception as e:
            logger.error(
                f"Error collecting data for {service_name} in region {region}: {str(e)}"
            )
            return service_name, None

    def collect_region_details(self, region: str) -> Dict[str, Any]:
        """Collect details for a specific region."""
        account_details = {
            "provider": "aws",
            "account_id": self.get_account_id(),
            "region": region,
            "collection_time": datetime.utcnow().isoformat(),
            "services": {},
        }

        logger.info(f"Starting AWS service data collection for region {region}")
        total_services = len(self.services)

        # Track running services
        running_services = set()
        completed_services = set()
        service_start_times = {}

        # Create batches of 3 services
        service_batches = [
            self.services[i : i + 10] for i in range(0, len(self.services), 10)
        ]

        def log_service_status():
            current_time = datetime.utcnow()
            logger.info(f"Current service status for region {region}:")
            for service_name in running_services:
                elapsed = current_time - service_start_times[service_name]
                logger.info(
                    f"  - {service_name} has been running for {elapsed.total_seconds():.1f} seconds"
                )

        with ThreadPoolExecutor(max_workers=3) as executor:
            with tqdm(
                total=total_services, desc=f"Collecting AWS service data for {region}"
            ) as pbar:
                for batch in service_batches:
                    # Submit batch of services to executor
                    futures = []
                    for service in batch:
                        service_name = service(self.get_session_for_region(region)).name
                        running_services.add(service_name)
                        service_start_times[service_name] = datetime.utcnow()
                        futures.append(
                            executor.submit(self.process_service, service, region)
                        )

                    # Wait for batch to complete with timeout
                    try:
                        for future in futures:
                            try:
                                service_name, data = future.result(
                                    timeout=300
                                )  # 5 minute timeout per service
                                if data:
                                    account_details["services"][service_name] = data
                                running_services.remove(service_name)
                                completed_services.add(service_name)
                                pbar.update(1)
                            except TimeoutError:
                                logger.error(
                                    f"Services still running after timeout in region {region}: {running_services}"
                                )
                                log_service_status()
                                pbar.update(1)
                            except Exception as e:
                                logger.error(
                                    f"Error processing services in region {region}: {str(e)}"
                                )
                                log_service_status()
                                pbar.update(1)
                    except Exception as e:
                        logger.error(
                            f"Batch processing error in region {region}: {str(e)}"
                        )
                        log_service_status()

                    # Log status after each batch
                    if running_services:
                        log_service_status()

        if running_services:
            logger.warning(
                f"Services that did not complete in region {region}: {running_services}"
            )
        logger.info(f"Completed services in region {region}: {completed_services}")
        logger.info(f"Completed AWS service data collection for region {region}")
        return account_details

    def generate_output(self) -> List[Dict[str, Any]]:
        """Generate output for all target regions."""
        all_regions_data = []

        for i, region in enumerate(self.target_regions):
            try:
                logger.info(f"Starting collection for region: {region}")
                region_data = self.collect_region_details(region)
                all_regions_data.append(region_data)
                logger.info(f"Completed collection for region: {region}")
            except Exception as e:
                logger.error(f"Error collecting data for region {region}: {str(e)}")

        return all_regions_data


class AzureProvider:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

        self.client = StorageManagementClient(
            credential=ClientSecretCredential(
                client_id=self.config.get("azure_client_id"),
                client_secret=self.config.get("azure_client_secret"),
                tenant_id=self.config.get("azure_tenant_id"),
            ),
            subscription_id=self.config.get("azure_subscription_id"),
        )

    def generate_output(self) -> List[Dict[str, Any]]:
        data = self.client.storage_accounts.list()
        items = []
        for account in data:
            items.append(
                {
                    "id": account.id,
                    "name": account.name,
                    "location": account.location,
                    "provisioning_state": account.provisioning_state,
                    "sku": account.sku,
                    "kind": account.kind,
                    "identity": account.identity,
                    "extended_location": account.extended_location,
                    "provisioning_state": account.provisioning_state,
                    "primary_endpoints": account.primary_endpoints,
                    "primary_location": account.primary_location,
                    "status_of_primary": account.status_of_primary,
                    "last_geo_failover_time": account.last_geo_failover_time,
                    "secondary_location": account.secondary_location,
                    "status_of_secondary": account.status_of_secondary,
                    "creation_time": account.creation_time,
                    "custom_domain": account.custom_domain,
                }
            )
        return items


def parse_args():
    parser = argparse.ArgumentParser(
        description="Collect service details and generate a JSON report."
    )
    parser.add_argument(
        "--provider",
        choices=["aws", "azure"],
        required=True,
        help="Provider to collect details from",
    )
    # Optional AWS arguments - environment variables will be used if not provided
    parser.add_argument(
        "--aws-access-key-id",
        help="AWS Access Key ID (can also be set via AWS_ACCESS_KEY_ID environment variable)",
    )
    parser.add_argument(
        "--aws-secret-access-key",
        help="AWS Secret Access Key (can also be set via AWS_SECRET_ACCESS_KEY environment variable)",
    )
    parser.add_argument(
        "--aws-session-token",
        help="AWS Session Token (can also be set via AWS_SESSION_TOKEN environment variable)",
    )
    parser.add_argument(
        "--region",
        help="AWS Region (can also be set via AWS_REGION or AWS_DEFAULT_REGION environment variable)",
    )
    parser.add_argument(
        "--role-arn",
        help="AWS Role ARN (can also be set via AWS_ROLE_ARN environment variable)",
    )
    parser.add_argument(
        "--application-id",
        help="Application ID (can also be set via APPLICATION_ID environment variable)",
    )
    parser.add_argument(
        "--source-id",
        help="Source ID (can also be set via SOURCE_ID environment variable)",
    )
    parser.add_argument(
        "--connection-id",
        help="Connection ID (can also be set via CONNECTION_ID environment variable)",
    )
    parser.add_argument(
        "--env",
        help="Environment (can also be set via ENV environment variable)",
    )
    parser.add_argument(
        "--azure-client-id",
        help="Azure Client ID (can also be set via AZURE_CLIENT_ID environment variable)",
    )
    parser.add_argument(
        "--azure-client-secret",
        help="Azure Client Secret (can also be set via AZURE_CLIENT_SECRET environment variable)",
    )
    parser.add_argument(
        "--azure-tenant-id",
        help="Azure Tenant ID (can also be set via AZURE_TENANT_ID environment variable)",
    )
    parser.add_argument(
        "--azure-subscription-id",
        help="Azure Subscription ID (can also be set via AZURE_SUBSCRIPTION_ID environment variable)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    try:
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)

        if args.provider == "aws":
            # Only include args in config if they were explicitly provided
            provider_config = {}
            if args.role_arn:
                provider_config["role_arn"] = args.role_arn
            if args.aws_access_key_id:
                provider_config["aws_access_key_id"] = args.aws_access_key_id
            if args.aws_secret_access_key:
                provider_config["aws_secret_access_key"] = args.aws_secret_access_key
            if (
                args.aws_session_token
                and args.aws_session_token != ""
                and args.aws_session_token != "aws_session_token"
            ):
                provider_config["aws_session_token"] = args.aws_session_token
            if args.region:
                provider_config["region"] = args.region

            provider = AWSProvider(provider_config)
            all_regions_data = provider.generate_output()

        elif args.provider == "azure":
            provider_config = {}
            provider_config["azure_client_id"] = args.azure_client_id or os.environ.get(
                "AZURE_CLIENT_ID"
            )
            provider_config["azure_client_secret"] = (
                args.azure_client_secret or os.environ.get("AZURE_CLIENT_SECRET")
            )
            provider_config["azure_tenant_id"] = args.azure_tenant_id or os.environ.get(
                "AZURE_TENANT_ID"
            )
            provider_config["azure_subscription_id"] = (
                args.azure_subscription_id or os.environ.get("AZURE_SUBSCRIPTION_ID")
            )
            provider = AzureProvider(provider_config)
            all_regions_data = provider.generate_output()

        else:
            print(f"Provider {args.provider} is not yet implemented")
            sys.exit(1)

        output_file = output_dir / f"{args.provider}_data.json"
        with open(output_file, "w") as f:
            json.dump(all_regions_data, f, indent=2, default=str)

        application_id = args.application_id or os.environ.get("APPLICATION_ID")
        current_source_id = args.source_id or os.environ.get("SOURCE_ID")
        connection_id = args.connection_id or os.environ.get("CONNECTION_ID")

        if (
            not application_id
            or application_id == ""
            or application_id == "application_id"
            or not connection_id
            or connection_id == ""
            or connection_id == "connection_id"
        ):
            logger.info("No application ID or source ID provided, skipping upload")
        else:
            url = app_config[env]["url"]
            endpoint = f"{url}/app/uploads/generate-presigned-url-internal?app_id={application_id}"

            if (
                current_source_id
                and current_source_id != ""
                and current_source_id != "source_id"
            ):
                endpoint += f"&source_id={current_source_id}"

            data = {
                "items": [
                    {
                        "file_type": "source_documents",
                        "file_name": output_file.name,
                        "fe_id": str(uuid.uuid4()),
                    }
                ]
            }

            response = requests.post(endpoint, json=data)

            presigned_url = response.json()["data"][0]["url"]

            uuid_pattern = re.compile(
                r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}"
            )
            uuids = uuid_pattern.findall(presigned_url)
            source_uuid = uuids[0]

            with open(output_file, "rb") as f:
                requests.put(presigned_url, data=f)

            url_2 = f"{url}/app/{application_id}/sources-internal?connection_id={connection_id}"
            data_2 = {
                "items": [
                    {
                        "control_ids": [],
                        "tags": [],
                        "uuid": source_uuid,
                    }
                ]
            }
            response_2 = requests.patch(url_2, json=data_2)

            logger.info(
                f"{args.provider} provider details have been written to {output_file}"
            )

    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
