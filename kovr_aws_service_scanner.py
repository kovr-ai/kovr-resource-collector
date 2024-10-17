from prowler.lib.cli.parser import ProwlerArgumentParser
from prowler.lib.check.models import CheckMetadata
from prowler.lib.check.compliance_models import Compliance
from prowler.lib.check.compliance import update_checks_metadata_with_compliance
from prowler.lib.check.checks_loader import load_checks_to_execute
from prowler.providers.common.provider import Provider
import importlib
import sys
from prowler.providers.common.models import Audit_Metadata
import json
from collections import defaultdict
from pydantic import BaseModel
from datetime import datetime
from tqdm import tqdm
import os
import shutil

# Define the output file name
aws_resource_combined_output_file = "aws_resources_combined.json"

# Increase recursion limit if necessary
sys.setrecursionlimit(15000)

# Initialize Argument Parser
parser = ProwlerArgumentParser()
args = parser.parse()

args.provider = 'aws'

Provider.set_global_provider(args)

# Save Arguments
provider = args.provider

# Initialize Provider
Provider.init_global_provider(args)
global_provider = Provider.get_global_provider()

global_provider.audit_metadata = Audit_Metadata(
    services_scanned=0,
    expected_checks=[],
    completed_checks=0,
    audit_progress=0,
)

if provider == "dashboard":
    from dashboard import DASHBOARD_ARGS
    from dashboard.__main__ import dashboard

    sys.exit(dashboard.run(**DASHBOARD_ARGS))

# Extract relevant arguments
checks = args.check
excluded_checks = args.excluded_check
excluded_services = args.excluded_service
services = args.service
categories = args.category
checks_file = args.checks_file
checks_folder = args.checks_folder
severities = args.severity
compliance_framework = args.compliance
custom_checks_metadata_file = args.custom_checks_metadata_file
default_execution = (
    not checks
    and not services
    and not categories
    and not excluded_checks
    and not excluded_services
    and not severities
    and not checks_file
    and not checks_folder
)

# Load checks metadata
bulk_checks_metadata = CheckMetadata.get_bulk(provider)

# Load compliance frameworks
bulk_compliance_frameworks = Compliance.get_bulk(provider)

# Update checks metadata with compliance frameworks
bulk_checks_metadata = update_checks_metadata_with_compliance(
    bulk_compliance_frameworks, bulk_checks_metadata
)

# Load checks to execute
checks_to_execute = load_checks_to_execute(
    bulk_checks_metadata,
    bulk_compliance_frameworks,
    checks_file,
    checks,
    services,
    severities,
    compliance_framework,
    categories,
    provider,
)

# Define output folder path
output_folder_path = './kovr-scan'

# Initialize metadata storage
meta_json_file = {}

# Create output folder if it doesn't exist
os.makedirs(output_folder_path, exist_ok=True)

# Recursive function to handle serialization
def class_to_dict(obj, seen=None):
    if seen is None:
        seen = set()

    if isinstance(obj, dict):
        new_dict = {}
        for key, value in obj.items():
            if isinstance(key, tuple):
                key = str(key)  # Convert tuple to string
            new_dict[key] = class_to_dict(value, seen)
        return new_dict
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, deque):
        return list(class_to_dict(item, seen) for item in obj)
    elif isinstance(obj, BaseModel):
        return obj.dict()
    elif isinstance(obj, (list, tuple)):
        return [class_to_dict(item, seen) for item in obj]
    elif hasattr(obj, "__dict__") and id(obj) not in seen:
        seen.add(id(obj))
        return {key: class_to_dict(value, seen) for key, value in obj.__dict__.items()}
    else:
        return obj

# Initialize a set to keep track of processed services
service_set = set()

# Initialize the combined output dictionary using defaultdict
combined_output_json = defaultdict(dict)

# Define the checks you want to execute (modify as needed)
for check_name in tqdm(checks_to_execute, desc="Aggregating Services"):
    try:
        # Extract the service name from the check name
        service = check_name.split("_")[0]
        
        if service in service_set:
            continue  # Skip if already processed
        
        service_set.add(service)

        # Define the path to the service's provider module
        service_path = f'./prowler/providers/aws/services/{service}'

        # List to store all _client.py filenames
        client_files = []

        # Walk through the service directory to find all _client.py files
        for root, dirs, files in os.walk(service_path):
            for file in files:
                if file.endswith('_client.py'):
                    client_files.append(file)

        # Define the service's output folder
        service_output_folder = f'{output_folder_path}/{service}'
        os.makedirs(service_output_folder, exist_ok=True)
        
        # Initialize the service's output structure
        # Structure: combined_output_json[service][extracted_key] = data
        # Example: combined_output_json["ec2"]["ec2"] = {...}, combined_output_json["ec2"]["additional"] = {...}
        
        for service_client in client_files:
            # Extract the module name without the .py extension
            service_client_module = service_client.split('.py')[0]
            
            # Define the module path for dynamic import
            check_module_path = f"prowler.providers.aws.services.{service}.{service_client_module}"
            
            try:
                # Dynamically import the service client module
                lib = importlib.import_module(f"{check_module_path}")
            except ModuleNotFoundError:
                print(f"Module not found: {check_module_path}. Skipping.")
                continue
            except Exception as e:
                print(f"Error importing module {check_module_path}: {e}. Skipping.")
                continue
            
            # Get the client class from the module
            client_class = getattr(lib, f"{service_client_module}")
            
            # Initialize metadata if not already present
            if not meta_json_file.get(f'{service}'):
                meta_json_file[f'{service}'] = []
            
            # Derive a unique key from the client module name
            # Example: "ec2_client" -> "ec2", "s3_objects_client" -> "s3_objects"
            if service_client_module.endswith('_client'):
                service_output_key = service_client_module[:-7]  # Remove '_client'
            else:
                service_output_key = service_client_module  # Use full name if no suffix

            # Append the JSON output file path to metadata
            meta_json_file[f'{service}'].append(f'./{service}/{service_output_key}_output.json')
            
            # Define the path to the output JSON file
            output_json_path = f'{service_output_folder}/{service_output_key}_output.json'
            
            # Get the output data by calling the __to_dict__() method
            output_data = client_class.__to_dict__()

            # Serialize the output data to JSON
            with open(output_json_path, 'w') as fp:
                json.dump(output_data, fp, default=str, indent=4)
                print(f"Written data to {output_json_path}")
            
            # Add the data to the combined output dictionary
            combined_output_json[service][service_output_key] = output_data

    except Exception as e:
        print(f"Exception while processing {check_name}: {e}")

# Write the metadata to output_metadata.json
with open(f'{output_folder_path}/output_metadata.json', 'w') as fp:
    json.dump(meta_json_file, fp, default=str, indent=4)
    print(f"Metadata written to {output_folder_path}/output_metadata.json")

# Print the combined output (optional)
#print(json.dumps(combined_output_json, indent=4))

# Write the combined output to the final JSON file
with open(f'{output_folder_path}/{aws_resource_combined_output_file}', 'w') as fp:
    json.dump(combined_output_json, fp, default=str, indent=4)
    print(f"Combined AWS resources written to {output_folder_path}/{aws_resource_combined_output_file}")

# Compress the output folder into a zip file
folder_to_compress = f'{output_folder_path}'
output_zip_file = f'{output_folder_path}/kovr-scan-compressed'  # The output file (without extension)

# Remove existing zip file if it exists
if os.path.exists(f'{output_zip_file}.zip'):
    os.remove(f'{output_zip_file}.zip')

# Compress the folder into a zip file
shutil.make_archive(f'{output_zip_file}', 'zip', folder_to_compress)
print(f"Compressed folder into {output_zip_file}.zip")