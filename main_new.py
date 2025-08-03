from con_mon.utils import sql, helpers
from con_mon.checks import get_checks_by_ids
from con_mon.connectors import get_connector_by_id, get_connector_input_by_id


def main(
    connection_id: int,
    connector_type: str,
    credentials: dict,
    customer_id: str,
    check_ids: list[int] | None = None,
    metadata: dict | None = None,
):
    checks_to_run = get_checks_by_ids(check_ids)
    connector_service = get_connector_by_id(connector_type)
    ConnectorInput = get_connector_input_by_id(connector_service)

    # Initialize GitHub connector
    connector_input = ConnectorInput(**credentials)
    resource_collection = connector_service.fetch_data(connector_input)

    print(f"✅ Retrieved {len(resource_collection.resources)} {connector_type} resources")

    # Execute checks and collect results
    executed_check_results = []
    for check_id, check_name, check_function in checks_to_run:
        check_results = check_function.evaluate(resource_collection)
        executed_check_results.append((check_id, check_name, check_results))

    # Generate SQL files from executed check results
    helpers.print_summary(
        executed_check_results=executed_check_results,
    )

    # Print comprehensive summary
    sql.insert_check_results(
        executed_check_results,
        resource_collection=resource_collection,
        customer_id=customer_id,
        connection_id=connection_id,
    )

def params_from_connection_id(
    connection_id: int,
    check_ids: list[int] | None = None,
):
    connector_type = 'github'
    credentials = dict(
        GITHUB_TOKEN='your-github-token-here',
    )
    metadata = dict()
    customer_id = 'kovr-customer-001',
    return (
        connection_id,
        connector_type,
        credentials,
        customer_id,
        check_ids,
        metadata,
    )


if __name__ == "__main__":
    main(
        *params_from_connection_id(
            1,
            check_ids=[],
        ),
    )
