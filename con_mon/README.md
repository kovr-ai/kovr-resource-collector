# con_mon - Continuous Monitoring Framework

A YAML-driven, type-safe framework for resource collection, validation, and monitoring across cloud providers and services.

## Architecture Overview

The con_mon framework consists of four main components:

1. **Resources** - Data models that define the structure of collected data
2. **Connectors** - Service definitions for fetching data from external providers
3. **Providers** - Implementation classes that actually collect and process data
4. **Checks** - Validation rules that evaluate collected resources

## Core Concepts

### Resource and ResourceCollection

Every data source must implement at minimum:
- A **Resource** model (inherits from base `Resource`)  
- A **ResourceCollection** model (inherits from base `ResourceCollection`)
- The provider's `process()` method must return a `ResourceCollection`

## GitHub Example

Here's how the GitHub implementation works as a complete example:

### 1. Resource Definition (`resources/resources.yaml`)

```yaml
github:
  resource_class: "GithubResource"
  collection_class: "GithubResourceCollection"
  
  # Define the main resource structure
  resource_fields:
    repository_data:
      type: "RepositoryData"
      description: "GitHub repository information"
    actions_data:
      type: "ActionsData" 
      description: "GitHub Actions workflow data"
    collaboration_data:
      type: "CollaborationData"
      description: "Repository collaboration information"
    security_data:
      type: "SecurityData"
      description: "Security and vulnerability data"
    organization_data:
      type: "OrganizationData"
      description: "Organization-level information"
    advanced_features_data:
      type: "AdvancedFeaturesData"
      description: "Advanced GitHub features usage"

  # Define nested data structures
  nested_models:
    RepositoryData:
      basic_info:
        type: "BasicInfo"
      branches:
        type: "List[Branch]"
      # ... more fields
```

### 2. Provider Implementation (`providers/gh/gh_provider.py`)

```python
@provider_class
class GitHubProvider(Provider):
    def __init__(self, metadata: dict):
        self.GITHUB_TOKEN = metadata["GITHUB_TOKEN"]
        super().__init__(Providers.GITHUB.value, metadata)

    def process(self) -> GithubResourceCollection:
        """Process data collection and return GitHubResourceCollection"""
        
        # 1. Collect raw data from GitHub API
        raw_data = self._fetch_github_data()
        
        # 2. Transform into GithubResource objects
        github_resources = []
        for repo_name, repo_data in raw_data.items():
            resource = GithubResource(
                name=repo_name,
                id=f"github-{repo_name.replace('/', '-')}",
                source_connector='github',
                repository_data=repo_data['repository'],
                actions_data=repo_data['actions'],
                # ... populate all data types
            )
            github_resources.append(resource)
        
        # 3. Return ResourceCollection (REQUIRED)
        return GithubResourceCollection(
            resources=github_resources,
            source_connector='github',
            total_count=len(github_resources),
            fetched_at=datetime.now(),
            collection_metadata={
                'api_version': 'v3',
                'authenticated_user': self._get_user(),
                # ... additional metadata
            }
        )
```

### 3. Connector Configuration (`connectors/connectors.yaml`)

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

### 4. Check Configuration (`checks/checks.yaml`)

```yaml
checks:
  - id: 1002
    name: "github_repository_private"
    description: "Verify that GitHub repository is private"
    field_path: "repository_data.basic_info.private"
    operation:
      name: "EQUAL"
    expected_value: true
```

## Key Requirements

### For Providers

1. **Inherit from `Provider`**: Use the `@provider_class` decorator
2. **Implement `process()` method**: Must return a `ResourceCollection` subclass
3. **Handle authentication**: Accept credentials via constructor metadata
4. **Error handling**: Gracefully handle API failures and rate limits

### For Resources

1. **Inherit from base classes**: `Resource` and `ResourceCollection`
2. **Define in YAML first**: Resources are dynamically generated from YAML
3. **Use proper field types**: Leverage nested Pydantic models for complex data
4. **Include metadata**: Add collection-level metadata for debugging and auditing

### For Data Flow

```
Provider.process() → ResourceCollection → Checks.evaluate() → Database
```

## Getting Started

1. **Define your resource structure** in `resources/resources.yaml`
2. **Create a provider class** that implements data collection
3. **Configure the connector** in `connectors/connectors.yaml`
4. **Write validation checks** in `checks/checks.yaml`
5. **Test with main_new.py** using your connection ID

## Best Practices

- **Keep providers focused**: One provider per service/API
- **Use nested models**: Break complex data into logical structures  
- **Handle errors gracefully**: Log errors but don't crash the collection
- **Include rich metadata**: Help with debugging and auditing
- **Follow naming conventions**: Use clear, descriptive names for resources and fields
- **Version your schemas**: Plan for API changes and data evolution

## Testing

```python
# Use main_new.py for testing
python3 main_new.py  # Uses connection ID 1 by default

# Or test specific checks
main(*params_from_connection_id(connection_id=1, check_ids=[1001, 1002]))
```

This architecture ensures type safety, YAML-driven configuration, and extensibility across different cloud providers and services. 