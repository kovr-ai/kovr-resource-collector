import os
from con_mon.utils import sql, helpers
from con_mon.checks import get_checks_by_ids
from con_mon.connectors import get_connector_by_id, get_connector_input_by_id
from con_mon.utils.db import get_db


def main(
    connection_id: int,
    connector_type: str,
    credentials: dict,
    customer_id: str,
    check_ids: list[int] | None = None,
    metadata: dict | None = None,
):
    checks_to_run = get_checks_by_ids(connection_id, check_ids)
    connector_service = get_connector_by_id(connector_type)
    ConnectorInput = get_connector_input_by_id(connector_service)

    # Initialize GitHub connector
    connector_input = ConnectorInput(**credentials)
    resource_collection = connector_service.fetch_data(connector_input)
    # from pdb import set_trace;set_trace()

    print(f"✅ Retrieved {len(resource_collection.resources)} {connector_type} resources")

    # Execute checks and collect results
    executed_check_results = []
    
    for check_id, check_name, check in checks_to_run:
        # Execute the check against all resources
        check_results = check.evaluate(resource_collection.resources)
        if check_results is not None:
            executed_check_results.append((check_id, check_name, check_results))

    # Generate SQL files from executed check results
    helpers.print_summary(
        executed_check_results=executed_check_results,
    )

    check_dicts = sql.get_check_dicts(
        executed_check_results,
        resource_collection=resource_collection
    )
    # return
    sql.insert_check_results(
        check_dicts,
        customer_id=customer_id,
        connection_id=connection_id,
    )

def params_from_connection_id(
    connection_id: int,
    check_ids: list[int] | None = None,
):
    """
    Fetch connection parameters from database by connection_id.

    Args:
        connection_id: ID of the connection record in the database
        check_ids: List of check IDs to run (optional)

    Returns:
        Tuple of (connection_id, connector_type, credentials, customer_id, check_ids, metadata)

    Raises:
        ValueError: If connection_id is not found or data is invalid
    """
    # Get database instance
    db = get_db()

    print(f"🔍 Fetching connection data for ID: {connection_id}")

    # Query to get connection data
    query_sql = """
    SELECT 
        id,
        customer_id,
        type,
        credentials,
        metadata,
        sync_status
    FROM connections 
    WHERE id = %s 
    AND is_deleted = FALSE;
    """

    try:
        results = db.execute_query(query_sql, (connection_id,))

        if not results:
            raise ValueError(f"Connection ID {connection_id} not found or has been deleted")

        connection = results[0]

        # Validate connection is active
        if connection['sync_status'] != 'active':
            print(f"⚠️ Warning: Connection {connection_id} status is '{connection['sync_status']}' (not active)")

        # Extract data from database record
        customer_id = connection['customer_id']
        credentials = connection['credentials']  # Already a dict from JSONB
        metadata = connection['metadata'] or {}  # Default to empty dict if None

        # Map connection type to connector type
        # Assuming type 1 = github, can be extended for other types
        type_mapping = {
            1: 'github',
            2: 'aws',
            # Add more mappings as needed
            # 3: 'azure',
        }

        connection_type = connection['type']
        if connection_type not in type_mapping:
            raise ValueError(f"Unsupported connection type: {connection_type}")

        connector_type = type_mapping[connection_type]

        print(f"✅ Connection data loaded:")
        print(f"   • Customer ID: {customer_id}")
        print(f"   • Connector Type: {connector_type}")
        print(f"   • Status: {connection['sync_status']}")
        print(f"   • Credentials: {list(credentials.keys())}")
        print(f"   • Metadata: {list(metadata.keys()) if metadata else 'No metadata'}")

        return (
            connection_id,
            connector_type,
            credentials,
            customer_id,
            check_ids,
            metadata,
        )

    except Exception as e:
        print(f"❌ Failed to fetch connection data: {e}")
        raise

def wrapper(message: dict = {}):
    # CONNECTOR_TYPE_SAMPLE_CONNECTION_IDS = {
    #     'aws': 35,
    #     'github': 26,
    # }
    # connection_id = CONNECTOR_TYPE_SAMPLE_CONNECTION_IDS['aws']
    # connection_id = CONNECTOR_TYPE_SAMPLE_CONNECTION_IDS['github']
    connection_id = message.get("CONNECTION_ID") or os.environ.get("CONNECTION_ID")
    check_ids_str = message.get("CHECK_IDS") or os.environ.get("CHECK_IDS")
    check_ids = check_ids_str.split(",") if check_ids_str else list()
    if not connection_id and not check_ids:
        return
    main(
        *params_from_connection_id(
            int(connection_id),
            [int(check_id)
             for check_id in check_ids],
        ),
    )

if __name__ == "__main__":
    wrapper()