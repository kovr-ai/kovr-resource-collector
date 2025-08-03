from con_mon.utils import sql, helpers
from con_mon.checks import get_checks_by_ids
from con_mon.connectors import get_connector_by_id, get_connector_input_by_id


def main(
    connector_type: str,
    metadata: dict,
    check_ids: list[int] | None = None,
):
    checks_to_run = get_checks_by_ids(check_ids)
    connector_service = get_connector_by_id(connector_type)
    ConnectorInput = get_connector_input_by_id(connector_service)

    # Initialize GitHub connector
    connector_input = ConnectorInput(**metadata)
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
        **metadata,
    )


if __name__ == "__main__":
    metadata = dict(
        GITHUB_TOKEN='your-github-token-here',
        customer_id='kovr-customer-001',
        connection_id=1,
    )
    main(
        connector_type='github',
        metadata=metadata,
        check_ids=[],
    )
