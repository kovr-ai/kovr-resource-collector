from con_mon.checks import (
    github_main_branch_protected,
    github_repository_private,
    github_minimum_branch_count
)
from con_mon.connectors import github as github_connector
from con_mon.connectors import GithubConnectorInput
from con_mon.utils import sql, helpers
import os

def main():
    """Main test function that runs checks and generates SQL files"""

    print("🔄 Starting GitHub checks test...")

    # Initialize GitHub connector with environment variable
    github_token = os.getenv('GITHUB_TOKEN', 'your-github-token-here')
    github_input = GithubConnectorInput(GITHUB_TOKEN=github_token)
    github_resource_collection = github_connector.fetch_data(github_input)

    print(f"✅ Retrieved {len(github_resource_collection.resources)} GitHub resources")

    # Define checks to run
    checks_to_run = [
        (1001, 'github_main_branch_protected', github_main_branch_protected),
        (1002, 'github_repository_private', github_repository_private),
        (1003, 'github_minimum_branch_count', github_minimum_branch_count)
    ]

    # Execute checks and collect results
    executed_check_results = []
    for check_id, check_name, check_function in checks_to_run:
        check_results = check_function.evaluate(github_resource_collection)
        executed_check_results.append((check_id, check_name, check_results))

    print(f"\n🔍 Running {len(checks_to_run)} checks and generating SQL files...")

    # Generate SQL files from executed check results
    helpers.print_summary(
        executed_check_results=executed_check_results,
    )

    # Print comprehensive summary
    sql.insert_check_results(
        executed_check_results,
        resource_collection=github_resource_collection,
        customer_id='kovr-customer-001',
        connection_id=1,
        output_dir='sql_output'
    )
    
    print("\n🎉 GitHub checks test completed!")


if __name__ == "__main__":
    main() 