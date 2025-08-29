# Connectors Module

The connectors module provides a YAML-driven framework for defining service integrations that fetch data from external providers like GitHub, AWS, Azure, etc.

## Overview

Connectors serve as the bridge between the con_mon framework and external data sources. They define:
- **Input requirements** (credentials, configuration)
- **Provider mapping** (which class handles the data collection)
- **Method specification** (which method to call for data fetching)

## Adding New Connectors

### 1. Define Connector in YAML (`connectors.yaml`)

```yaml
my_service:  # Connector identifier (used in code)
  input:
    # Define required input fields and their types
    API_KEY: "string"
    REGION: "string"
    ENDPOINT_URL: "string"
  
  connectors:
    name: "My Service"  # Human-readable name
    description: "Description of what this connector does"
    connector_type: "api"  # Type: api, database, file, etc.
    provider_service: "providers.my_service.my_provider"  # Python module path
    method: "process"  # Method name to call (usually 'process')
```

### 2. Implementation Requirements

#### Input Class (Auto-generated)
The YAML configuration automatically creates a Pydantic input class:
```python
# Generated as: MyServiceConnectorInput
# Usage:
input_config = MyServiceConnectorInput(
    API_KEY="your-api-key",
    REGION="us-east-1", 
    ENDPOINT_URL="https://api.myservice.com"
)
```

#### Provider Class
Create a provider class that implements the actual data collection:
```python
# providers/my_service/my_provider.py
from core.base_provider import Provider, provider_class
from core.models import Providers

@provider_class
class MyServiceProvider(Provider):
    def __init__(self, metadata: dict):
        # Extract credentials from metadata
        self.API_KEY = metadata["API_KEY"]
        self.REGION = metadata["REGION"]
        self.ENDPOINT_URL = metadata["ENDPOINT_URL"]
        
        super().__init__(Providers.MY_SERVICE.value, metadata)
    
    def process(self) -> MyServiceResourceCollection:
        """Collect data and return ResourceCollection"""
        
        # 1. Use credentials to connect to service
        client = self._create_client()
        
        # 2. Fetch raw data
        raw_data = client.fetch_all_resources()
        
        # 3. Transform to Resource objects
        resources = []
        for item in raw_data:
            resource = MyServiceResource(
                name=item['name'],
                id=f"myservice-{item['id']}",
                source_connector='my_service',
                # Map service-specific fields
                service_data=item['data'],
                metadata=item.get('metadata', {})
            )
            resources.append(resource)
        
        # 4. Return ResourceCollection (REQUIRED)
        return MyServiceResourceCollection(
            resources=resources,
            source_connector='my_service',
            total_count=len(resources),
            fetched_at=datetime.now(),
            collection_metadata={
                'api_version': client.api_version,
                'region': self.REGION,
                'endpoint': self.ENDPOINT_URL
            }
        )
    
    def _create_client(self):
        """Helper method to create API client"""
        return MyServiceClient(
            api_key=self.API_KEY,
            region=self.REGION,
            endpoint=self.ENDPOINT_URL
        )
```

### 3. Provider Registration
Update the Providers enum to include your new service:
```python
# core/models.py
class Providers(Enum):
    GITHUB = "github"
    MY_SERVICE = "my_service"  # Add new provider
    # ... other providers
```

## Real Examples

### GitHub Connector (Existing)
```yaml
github:
  input:
    GITHUB_TOKEN: "string"
  
  connectors:
    name: "GitHub"
    description: "GitHub repository and organization data collector"
    connector_type: "api"
    provider_service: "providers.gh.gh_provider"
    method: "process"
```

### AWS Connector Example
```yaml
aws:
  input:
    AWS_ACCESS_KEY_ID: "string"
    AWS_SECRET_ACCESS_KEY: "string"
    AWS_REGION: "string"
  
  connectors:
    name: "Amazon Web Services"
    description: "AWS resource collector for EC2, S3, RDS, etc."
    connector_type: "cloud"
    provider_service: "providers.aws.aws_provider"
    method: "process"
```

### Database Connector Example
```yaml
postgresql:
  input:
    DATABASE_URL: "string"
    DATABASE_NAME: "string"
    USERNAME: "string"
    PASSWORD: "string"
  
  connectors:
    name: "PostgreSQL"
    description: "PostgreSQL database metrics and schema collector"
    connector_type: "database"
    provider_service: "providers.postgresql.pg_provider"
    method: "process"
```

## Connector Usage

### Programmatic Access
```python
from con_mon.connectors import get_connector_by_id, get_connector_input_by_id

# Get connector service
connector_service = get_connector_by_id('github')

# Get input class
GithubConnectorInput = get_connector_input_by_id('github')

# Create input configuration
input_config = GithubConnectorInput(GITHUB_TOKEN='your-token')

# Fetch data
resource_collection = connector_service.fetch_data(input_config)
```

### Database-Driven Configuration
```python
# Using connection ID from database (main_new.py approach)
connection_id, connector_type, credentials, customer_id, check_ids, metadata = \
    params_from_connection_id(connection_id=1)

connector_service = get_connector_by_id(connector_type)
ConnectorInput = get_connector_input_by_id(connector_service)
connector_input = ConnectorInput(**credentials)
resource_collection = connector_service.fetch_data(connector_input)
```

## Best Practices

### Connector Design
- **Single Responsibility**: One connector per service/API
- **Clear Naming**: Use consistent, descriptive names
- **Standard Interface**: Always implement `process()` method returning ResourceCollection
- **Error Handling**: Handle authentication, rate limiting, and API errors gracefully

### Input Configuration
- **Required Fields Only**: Don't include optional fields in input spec
- **Clear Field Names**: Use standard naming conventions (API_KEY, not api_key)
- **Type Safety**: Currently supports "string" type, plan for expansion
- **Credential Security**: Never hardcode credentials in YAML

### Provider Implementation
- **Authentication First**: Validate credentials early in `__init__`
- **Robust Error Handling**: Log errors but continue processing when possible
- **Efficient Data Fetching**: Use pagination, bulk operations, and caching
- **Rich Metadata**: Include API versions, regions, timestamps in collection metadata

### Integration Points
- **Resource Models**: Ensure your provider returns the correct ResourceCollection type
- **Provider Enum**: Register new providers in the Providers enum
- **Module Structure**: Follow the `providers/{service}/{service}_provider.py` pattern

## Error Handling

The connector framework handles various error conditions:

### Connection Errors
```python
try:
    connector_service = get_connector_by_id('nonexistent')
except ValueError as e:
    print(f"Connector not found: {e}")
```

### Input Validation Errors
```python
try:
    input_config = GithubConnectorInput()  # Missing required GITHUB_TOKEN
except ValidationError as e:
    print(f"Invalid input: {e}")
```

### Provider Errors
```python
# In provider process() method
try:
    data = api_client.fetch_data()
except APIError as e:
    logger.error(f"API error: {e}")
    # Return empty collection or partial results
    return MyServiceResourceCollection(resources=[], ...)
```

## Advanced Configuration

### Custom Input Types
Future support for more input types:
```yaml
# Planned features
my_service:
  input:
    api_key: "string"
    port: "integer"
    enable_ssl: "boolean"
    endpoints: "array"
    config: "object"
```

### Connection Pooling
For providers that support connection pooling:
```python
class MyProvider(Provider):
    _connection_pool = None
    
    def __init__(self, metadata: dict):
        if not self._connection_pool:
            self._connection_pool = create_connection_pool(metadata)
        super().__init__(...)
```

### Rate Limiting
For APIs with rate limits:
```python
class MyProvider(Provider):
    def process(self):
        with RateLimiter(requests_per_second=10):
            return self._fetch_data()
```

## Testing Connectors

### Unit Testing
```python
def test_my_connector():
    input_config = MyServiceConnectorInput(
        API_KEY="test-key",
        REGION="test-region"
    )
    
    connector = get_connector_by_id('my_service')
    result = connector.fetch_data(input_config)
    
    assert isinstance(result, MyServiceResourceCollection)
    assert len(result.resources) > 0
```

### Integration Testing
```python
# Test with real credentials (use environment variables)
def test_my_connector_integration():
    input_config = MyServiceConnectorInput(
        API_KEY=os.getenv('MY_SERVICE_API_KEY'),
        REGION=os.getenv('MY_SERVICE_REGION')
    )
    
    connector = get_connector_by_id('my_service')
    result = connector.fetch_data(input_config)
    
    # Validate real data structure
    assert result.total_count >= 0
    assert result.source_connector == 'my_service'
```

This modular connector system makes it easy to add new data sources while maintaining consistency and type safety across the entire framework. 