"""Test that all dynamic imports work correctly."""

def test_imports():
    """Try importing all possible paths from our dynamic mapping system."""
    successful_imports = []
    failed_imports = []

    # List of all expected imports
    imports_to_test = [
        # Base mappings
        "from con_mon_v2 import mappings",
        
        # GitHub imports
        "from con_mon_v2.mappings.github import GithubConnectorService",
        "from con_mon_v2.mappings.github import GithubConnectorInput",
        "from con_mon_v2.mappings.github import github_connector_service",
        "from con_mon_v2.mappings.github import GithubResource",
        "from con_mon_v2.mappings.github import GithubResourceCollection",

        # AWS imports
        "from con_mon_v2.mappings.aws import AwsConnectorService",
        "from con_mon_v2.mappings.aws import AwsConnectorInput",
        "from con_mon_v2.mappings.aws import aws_connector_service",
        "from con_mon_v2.mappings.aws import EC2Resource",
        "from con_mon_v2.mappings.aws import S3Resource",
        "from con_mon_v2.mappings.aws import IAMResource",
        "from con_mon_v2.mappings.aws import CloudTrailResource",
        "from con_mon_v2.mappings.aws import CloudWatchResource",
        "from con_mon_v2.mappings.aws import AwsResourceCollection"
    ]

    print("\nTesting imports...")
    for import_stmt in imports_to_test:
        try:
            exec(import_stmt)
            successful_imports.append(import_stmt)
            print(f"✅ {import_stmt}")
        except ImportError as e:
            failed_imports.append((import_stmt, str(e)))
            print(f"❌ {import_stmt}")
            print(f"   Error: {str(e)}")

    # Print summary
    print("\nImport Test Summary:")
    print(f"Total imports tested: {len(imports_to_test)}")
    print(f"Successful imports: {len(successful_imports)}")
    print(f"Failed imports: {len(failed_imports)}")

    if failed_imports:
        print("\nFailed imports details:")
        for stmt, error in failed_imports:
            print(f"\n{stmt}")
            print(f"Error: {error}")


if __name__ == "__main__":
    test_imports()
