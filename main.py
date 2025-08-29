import argparse
from datetime import datetime
from collector import Collector
import json
import boto3
import os
import requests
import time

from rule_engine import RuleEngine

app_config = {
    "dev": {
        "url": "https://dev.kovrai.com/api/v1",
    },
    "qa": {
        "url": "https://qa.kovrai.com/api/v1",
    },
    "prod": {
        "url": "https://app.kovrai.com/api/v1",
    },
    "local": {
        "url": "http://localhost:3000/api/v1",
    },
}


def datetime_json_encoder(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def upload_json_to_s3(file_path, bucket_name, key):
    s3_client = boto3.client("s3")
    # s3 = session.resource("s3")
    # return s3.meta.client.upload_file(file_path, bucket_name, key)
    return s3_client.upload_file(file_path, bucket_name, key)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Collect service details and generate a JSON report."
    )
    parser.add_argument(
        "--provider",
        help="Provider to collect details from",
    )
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
        "--aws-external-id",
        help="AWS External ID (can also be set via AWS_EXTERNAL_ID environment variable)",
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
    args = parser.parse_args()
    return {
        "provider": args.provider or os.getenv("PROVIDER"),
        "metadata": {
            "AWS_ACCESS_KEY_ID": args.aws_access_key_id
            or os.getenv("KOVR_AWS_ACCESS_KEY_ID"),
            "AWS_SECRET_ACCESS_KEY": args.aws_secret_access_key
            or os.getenv("KOVR_AWS_SECRET_ACCESS_KEY"),
            "AWS_SESSION_TOKEN": args.aws_session_token
            or os.getenv("KOVR_AWS_SESSION_TOKEN"),
            "REGIONS": ["us-west-2"],
            "AWS_ROLE_ARN": args.role_arn or os.getenv("AWS_ROLE_ARN"),
            "AWS_EXTERNAL_ID": args.aws_external_id or os.getenv("AWS_EXTERNAL_ID"),
            "AZURE_CLIENT_ID": args.azure_client_id
            or os.getenv("AZURE_CLIENT_ID"),
            "AZURE_CLIENT_SECRET": args.azure_client_secret
            or os.getenv("AZURE_CLIENT_SECRET"),
            "AZURE_TENANT_ID": args.azure_tenant_id
            or os.getenv("AZURE_TENANT_ID"),
            "AZURE_SUBSCRIPTION_ID": args.azure_subscription_id
            or os.getenv("AZURE_SUBSCRIPTION_ID"),
        },
        "env": args.env or os.getenv("ENV"),
        "connection_id": args.connection_id or os.getenv("CONNECTION_ID"),
    }


if __name__ == "__main__":
    # while True:
    #     time.sleep(10)
    sts_client = boto3.client("sts")
    response = sts_client.get_caller_identity()
    print(response)
    args = parse_args()
    env = args["env"]
    app_config = app_config[env]

    collector = Collector(args["provider"], args["metadata"])
    response = collector.process()
    response_file_path = f"{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}_response.json"
    with open(response_file_path, "w") as f:
        json.dump(response, f, indent=4, default=datetime_json_encoder)
    upload_json_to_s3(response_file_path, "kovr-app-file-uploads-dev", response_file_path)
    print(f"Response uploaded to: {response_file_path}")

    if args["provider"] == "aws":
        rule_engine = RuleEngine(args["provider"], response)
        report = rule_engine.process()
    elif args["provider"] == "azure":
        rule_engine = RuleEngine(args["provider"], response)
        report = rule_engine.process()
    else:
        report = {}
    
    report_file_path = f"{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}_report.json"
    with open(report_file_path, "w") as f:
        json.dump(report, f, indent=4, default=datetime_json_encoder)
    upload_json_to_s3(report_file_path, "kovr-app-file-uploads-dev", report_file_path)
    print(f"Report uploaded to: {report_file_path}")

    url = app_config["url"] + f"/connections/{args['connection_id']}/connection-status"
    response = requests.post(
        url,
        json={
            "status": "completed",
            "response_file_path": response_file_path,
            "report_file_path": report_file_path,
        },
    )

    print(response.json())
