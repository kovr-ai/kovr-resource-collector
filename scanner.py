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
from tqdm import tqdm
import os

aws_resource_combined_output_file = "result.json"

sys.setrecursionlimit(15000)

parser = ProwlerArgumentParser()
args = parser.parse()

print(args)

Provider.set_global_provider(args)

provider = args.provider

if provider not in ["aws"]:
    print("Invalid provider")
    sys.exit(1)

Provider.init_global_provider(args)
global_provider = Provider.get_global_provider()

global_provider.audit_metadata = Audit_Metadata(
    services_scanned=0,
    expected_checks=[],
    completed_checks=0,
    audit_progress=0,
)

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

bulk_checks_metadata = CheckMetadata.get_bulk(provider)
bulk_compliance_frameworks = Compliance.get_bulk(provider)
bulk_checks_metadata = update_checks_metadata_with_compliance(
    bulk_compliance_frameworks, bulk_checks_metadata
)

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

output_folder_path = f"./result"

os.makedirs(output_folder_path, exist_ok=True)

service_set = set()

combined_output_json = []

checks_to_execute = ["ec2", "cloudwatch"]

for check_name in tqdm(checks_to_execute, desc="Aggregating Services"):
    try:
        service = check_name.split("_")[0]

        if service in service_set:
            continue

        service_set.add(service)

        service_path = f"./prowler/providers/aws/services/{service}"

        client_files = []

        for root, dirs, files in os.walk(service_path):
            for file in files:
                if file.endswith("_client.py"):
                    client_files.append(file)

        for service_client in client_files:
            service_client_module = service_client.split(".py")[0]

            check_module_path = (
                f"prowler.providers.aws.services.{service}.{service_client_module}"
            )

            try:
                lib = importlib.import_module(f"{check_module_path}")
            except ModuleNotFoundError:
                print(f"Module not found: {check_module_path}. Skipping.")
                continue
            except Exception as e:
                print(f"Error importing module {check_module_path}: {e}. Skipping.")
                continue

            client_class = getattr(lib, f"{service_client_module}")

            output_data = client_class.__to_dict__()

            combined_output_json.append(output_data)

    except Exception as e:
        print(f"Exception while processing {check_name}: {e}")

with open(f"{output_folder_path}/{aws_resource_combined_output_file}", "w") as fp:
    json.dump(combined_output_json, fp, default=str, indent=4)
    print(
        f"Combined AWS resources written to {output_folder_path}/{aws_resource_combined_output_file}"
    )

# Print content of the file
with open(f"{output_folder_path}/{aws_resource_combined_output_file}", "r") as fp:
    print(fp.read())
