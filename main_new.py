import os
from con_mon.compliance.data_loader import ChecksLoader, ConnectionLoader
from con_mon.compliance.models import Connection
from con_mon.utils.services import ResourceCollectionService, ConMonResultService
from con_mon.utils import helpers


def main(
    connection_id: int,
    connector_type: str,
    credentials: dict,
    customer_id: str,
    check_ids: list[int] | None = None,
    metadata: dict | None = None,
):
    # Use ResourceCollectionService for connector access
    service = ResourceCollectionService(connector_type)
    info_data, resource_collection = service.get_resource_collection(credentials)

    print(f"✅ Retrieved {len(resource_collection.resources)} {connector_type} resources")

    # Load checks using con_mon ChecksLoader
    checks_loader = ChecksLoader()
    if check_ids:
        checks = checks_loader.load_by_ids(check_ids)
    else:
        checks = checks_loader.load_all()

    print(f"✅ Loaded {len(checks)} checks from database")

    connection_loader = ConnectionLoader()
    connection_loader.update_connection_data(
        connection_id, info_data
    )
    # Execute checks and collect results
    executed_check_results = []
    filtered_checks = ChecksLoader.filter_by_resource_model(
        checks,
        resource_collection.resource_models
    )
    
    for check in filtered_checks:
        # Execute the check against all resources
        check_results = check.evaluate(resource_collection.resources)
        if check_results is not None:
            executed_check_results.append((check, check_results))

    # Generate summary using con_mon helpers with Check objects
    helpers.print_summary(executed_check_results)

    total_result_count = ConMonResultService.insert_in_db(
        executed_check_results=executed_check_results,
        customer_id=customer_id,
        connection_id=connection_id
    )
    
    print("\n💾 **Database Storage:**")
    print(f"   • Customer ID: {customer_id}")
    print(f"   • Connection ID: {connection_id}")
    print(f"   • Checks executed: {len(executed_check_results)}")
    print(f"   • Results Inserted: {total_result_count}")


def params_from_connection_id(
    connection_id: int,
    check_ids: list[int] | None = None,
):
    """
    Fetch connection parameters from database by connection_id using ConnectionLoader.

    Args:
        connection_id: ID of the connection record in the database
        check_ids: List of check IDs to run (optional)

    Returns:
        Tuple of (connection_id, connector_type, credentials, customer_id, check_ids, metadata)

    Raises:
        ValueError: If connection_id is not found or data is invalid
    """
    print(f"🔍 Fetching connection data for ID: {connection_id}")

    # Use ConnectionLoader to fetch connection data
    connection_loader = ConnectionLoader()
    
    # Load the specific connection by ID
    connection: Connection = connection_loader.load_by_ids([connection_id])[0]

    # Validate connection is active
    if connection.sync_status != 'active':
        print(f"⚠️ Warning: Connection {connection_id} status is '{connection.sync_status}' (not active)")

    # Extract data from Connection object
    customer_id = connection.customer_id
    credentials = connection.credentials  # Already a dict from JSONB
    metadata = connection.metadata or {}  # Default to empty dict if None

    print("✅ Connection data loaded:")
    print(f"   • Customer ID: {customer_id}")
    print(f"   • Status: {connection.sync_status}")
    print(f"   • Credentials: {list(credentials.keys())}")
    print(f"   • Metadata: {list(metadata.keys()) if metadata else 'No metadata'}")

    return (
        connection_id,
        connection.connector_type_str,
        credentials,
        customer_id,
        check_ids,
        metadata,
    )


if __name__ == "__main__":
    connection_id = os.environ.get("CONNECTION_ID")
    check_ids_str = os.environ.get("CHECK_IDS")
    check_ids = check_ids_str.split(",") if check_ids_str else list()
    main(
        *params_from_connection_id(
            int(connection_id),
            [int(check_id)
             for check_id in check_ids],
        ),
    )
