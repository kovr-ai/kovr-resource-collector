# Kovr Resource Collector

The Kovr Resource Collector is a comprehensive tool designed to scan and collect cloud infrastructure resources across multiple cloud providers. It generates detailed reports of your cloud infrastructure that can be uploaded to Kovr as a source.

## Features

- Multi-cloud resource scanning (currently supports AWS)
- Comprehensive resource inventory collection
- Parallel processing for efficient data collection
- Detailed resource configuration capture
- Compatible with Kovr's Sources UI
- Generates structured JSON output
- Support for cross-account access using IAM roles

## AWS Services Covered

The collector scans a wide range of AWS services, including but not limited to:

- EC2 (Instances, Security Groups, Volumes)
- IAM (Users, Roles, Policies)
- S3 (Buckets, Policies)
- KMS (Keys, Aliases)
- RDS (Databases, Snapshots)
- Lambda Functions
- VPC Resources
- ECS/EKS Clusters
- DynamoDB Tables
- CloudWatch (Alarms, Logs)
- And many more...

## Prerequisites

- Python 3.x
- AWS credentials with appropriate permissions
- pip (Python package manager)
- curl (for script download)

## Required Python Packages

```ini
boto3>=1.26.0
pytest==8.0.2
python-json-logger==2.0.7
pydantic==1.10.13
tqdm>=4.65.0
```

## Installation & Usage

### Quick Start

1. Set your AWS credentials as environment variables:
   ```bash
   export AWS_ACCESS_KEY_ID="your_access_key"
   export AWS_SECRET_ACCESS_KEY="your_secret_key"
   export AWS_SESSION_TOKEN="your_session_token"  # if using temporary credentials
   ```

2. Run the collector with a single command:
   ```bash
   curl -s https://raw.githubusercontent.com/kovr-ai/kovr-resource-collector/main/data_collector_script.sh | bash
   ```

### Manual Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/kovr-ai/kovr-resource-collector.git
   cd kovr-resource-collector
   ```

2. Install required packages:
   ```bash
   pip install -r data_collector_requirements.txt
   ```

3. Run the collector:
   ```bash
   python data_collector.py --provider aws
   ```

### Additional Options

The collector supports several command-line arguments:

```bash
python data_collector.py --provider aws [OPTIONS]

Options:
  --aws-access-key-id TEXT        AWS Access Key ID
  --aws-secret-access-key TEXT    AWS Secret Access Key
  --aws-session-token TEXT        AWS Session Token
  --region TEXT                   Specific AWS region to scan
  --role-arn TEXT                 AWS Role ARN for cross-account access
```

## Output

The collector generates a JSON file in the `output` directory containing detailed information about your cloud resources. This file can be directly uploaded to Kovr as a source.

### Output Structure
