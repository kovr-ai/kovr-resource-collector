# Resources Module

The resources module provides a YAML-driven framework for defining data models that represent collected resources from external providers. All resource models are dynamically generated from YAML configurations using Pydantic for type safety and validation.

## Overview

Resources define the structure of data collected from external sources. The module automatically generates:
- **Individual Resource models** (e.g., `GithubResource`, `AwsResource`)
- **Resource Collection models** (e.g., `GithubResourceCollection`)
- **Nested data models** for complex structures
- **Type-safe field definitions** with validation

## Adding New Resources

### 1. Define Resource in YAML (`resources.yaml`)

```yaml
my_service:  # Service identifier
  resource_class: "MyServiceResource"        # Main resource class name
  collection_class: "MyServiceResourceCollection"  # Collection class name
  
  # Define fields for the main resource
  resource_fields:
    primary_data:
      type: "PrimaryData"
      description: "Main service data"
    metadata_info:
      type: "MetadataInfo" 
      description: "Service metadata and configuration"
    usage_stats:
      type: "UsageStats"
      description: "Usage statistics and metrics"
  
  # Define nested model structures
  nested_models:
    PrimaryData:
      name:
        type: "str"
        description: "Resource name"
      status:
        type: "str"
        description: "Current status"
      created_at:
        type: "str"
        description: "Creation timestamp"
    
    MetadataInfo:
      region:
        type: "str"
        description: "Deployment region"
      tags:
        type: "List[str]"
        description: "Resource tags"
      
    UsageStats:
      requests_per_hour:
        type: "int"
        description: "Hourly request count"
      error_rate:
        type: "float"
        description: "Error rate percentage"
```

### 2. Generated Models

The YAML configuration automatically generates these Pydantic models:

```python
# Generated classes (automatically available after YAML processing):

class PrimaryData(BaseModel):
    name: str
    status: str
    created_at: str

class MetadataInfo(BaseModel):
    region: str
    tags: List[str]

class UsageStats(BaseModel):
    requests_per_hour: int
    error_rate: float

class MyServiceResource(Resource):  # Inherits from base Resource
    primary_data: PrimaryData
    metadata_info: MetadataInfo
    usage_stats: UsageStats

class MyServiceResourceCollection(ResourceCollection):  # Inherits from base ResourceCollection 
    resources: List[MyServiceResource]
    # Inherits: source_connector, total_count, fetched_at, collection_metadata
```

## Real Examples

### GitHub Resource (Existing)
```yaml
github:
  resource_class: "GithubResource"
  collection_class: "GithubResourceCollection"
  
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

  nested_models:
    RepositoryData:
      basic_info:
        type: "BasicInfo"
        description: "Basic repository information"
      branches:
        type: "List[Branch]"
        description: "Repository branches"
      stats:
        type: "RepoStats"
        description: "Repository statistics"
    
    BasicInfo:
      name:
        type: "str"
        description: "Repository name"
      private:
        type: "bool"
        description: "Is repository private"
      default_branch:
        type: "str"
        description: "Default branch name"
    
    Branch:
      name:
        type: "str"
        description: "Branch name"
      protected:
        type: "bool"
        description: "Is branch protected"
      commit_sha:
        type: "str"
        description: "Latest commit SHA"
```

### AWS Resource Example
```yaml
aws:
  resource_class: "AwsResource"
  collection_class: "AwsResourceCollection"
  
  resource_fields:
    ec2_data:
      type: "EC2Data"
      description: "EC2 instance information"
    s3_data:
      type: "S3Data"
      description: "S3 bucket information"
    rds_data:
      type: "RDSData"
      description: "RDS database information"
    billing_data:
      type: "BillingData"
      description: "Cost and billing information"

  nested_models:
    EC2Data:
      instances:
        type: "List[EC2Instance]"
        description: "List of EC2 instances"
      security_groups:
        type: "List[SecurityGroup]"
        description: "Security groups"
    
    EC2Instance:
      instance_id:
        type: "str"
        description: "Instance ID"
      instance_type:
        type: "str"
        description: "Instance type (e.g., t3.micro)"
      state:
        type: "str"
        description: "Instance state"
      tags:
        type: "Dict[str, str]"
        description: "Instance tags"
```

## Supported Field Types

### Basic Types
- `str` - String values
- `int` - Integer numbers
- `float` - Floating point numbers  
- `bool` - Boolean true/false
- `datetime` - Date and time objects

### Collection Types
- `List[Type]` - List of specified type
- `Dict[str, Type]` - Dictionary with string keys
- `Optional[Type]` - Optional field (can be None)

### Complex Types
- `CustomModel` - Reference to nested model defined in `nested_models`
- `Any` - Any type (use sparingly)

### Examples
```yaml
nested_models:
  MyModel:
    # Basic types
    name: { type: "str" }
    count: { type: "int" }
    rate: { type: "float" }
    enabled: { type: "bool" }
    
    # Collection types  
    items: { type: "List[str]" }
    metadata: { type: "Dict[str, str]" }
    optional_field: { type: "Optional[str]" }
    
    # Nested models
    config: { type: "ConfigModel" }
    services: { type: "List[ServiceModel]" }
```

## Base Classes

### Resource (Base)
All resource models inherit from the base `Resource` class:
```python
class Resource(BaseModel):
    id: str                    # Unique identifier
    name: str                  # Human-readable name
    source_connector: str      # Which connector collected this
    # + your custom fields from YAML
```

### ResourceCollection (Base)  
All collection models inherit from the base `ResourceCollection` class:
```python
class ResourceCollection(BaseModel):
    resources: List[Resource]           # List of collected resources
    source_connector: str               # Which connector collected this
    total_count: int                   # Total number of resources
    fetched_at: Optional[datetime]     # When collection happened
    collection_metadata: Dict[str, Any] = {}  # Additional metadata
    # + your custom collection fields (if any)
```

## Usage in Providers

### Creating Resources
```python
# In your provider's process() method
def process(self) -> MyServiceResourceCollection:
    # 1. Fetch raw data
    raw_data = self._fetch_from_api()
    
    # 2. Transform to resource objects
    resources = []
    for item in raw_data:
        resource = MyServiceResource(
            # Base Resource fields (required)
            id=f"myservice-{item['id']}",
            name=item['name'],
            source_connector='my_service',
            
            # Your custom fields from YAML
            primary_data=PrimaryData(
                name=item['name'],
                status=item['status'],
                created_at=item['created_at']
            ),
            metadata_info=MetadataInfo(
                region=item['region'],
                tags=item.get('tags', [])
            ),
            usage_stats=UsageStats(
                requests_per_hour=item['stats']['requests'],
                error_rate=item['stats']['errors']
            )
        )
        resources.append(resource)
    
    # 3. Return collection
    return MyServiceResourceCollection(
        resources=resources,
        source_connector='my_service',
        total_count=len(resources),
        fetched_at=datetime.now(),
        collection_metadata={
            'api_version': '2.0',
            'region': self.REGION,
            'collection_time': datetime.now().isoformat()
        }
    )
```

## Best Practices

### Resource Design
- **Logical Grouping**: Group related data into nested models
- **Clear Naming**: Use descriptive names for fields and models
- **Consistent Structure**: Follow patterns from existing resources
- **Appropriate Types**: Use specific types rather than generic `Any`

### Data Organization
```yaml
# Good: Organized by functional areas
resource_fields:
  basic_info:        # Core identification
  configuration:     # Settings and config
  runtime_data:      # Current state/metrics
  security_info:     # Security-related data

# Avoid: Flat structure with many top-level fields
resource_fields:
  name: { type: "str" }
  status: { type: "str" }
  region: { type: "str" }
  # ... many more fields
```

### Nested Models
- **Reusable Components**: Create models that can be reused across resources
- **Logical Hierarchy**: Nest related data together
- **Avoid Deep Nesting**: Keep nesting to reasonable levels (2-3 levels max)

### Field Definitions
```yaml
# Good: Include descriptions
name:
  type: "str"
  description: "Human-readable resource name"

# Acceptable: Type only for simple cases
count:
  type: "int"
```

## Integration with Checks

Resources work seamlessly with the checks framework:
```yaml
# In checks.yaml - referencing resource fields
- id: 2001
  name: "service_is_active"
  field_path: "primary_data.status"  # Accesses MyServiceResource.primary_data.status
  operation:
    name: "EQUAL"
  expected_value: "active"

- id: 2002
  name: "low_error_rate"
  field_path: "usage_stats.error_rate"  # Accesses MyServiceResource.usage_stats.error_rate
  operation:
    name: "LESS_THAN"
  expected_value: 5.0
```

## Testing Resources

### Validation Testing
```python
def test_resource_validation():
    # Test valid resource creation
    resource = MyServiceResource(
        id="test-1",
        name="Test Resource",
        source_connector="my_service",
        primary_data=PrimaryData(
            name="test",
            status="active",
            created_at="2023-01-01T00:00:00Z"
        ),
        # ... other required fields
    )
    
    assert resource.id == "test-1"
    assert resource.primary_data.status == "active"

def test_resource_validation_errors():
    # Test validation errors
    with pytest.raises(ValidationError):
        MyServiceResource(
            # Missing required fields
            id="test-1"
        )
```

### Collection Testing
```python
def test_collection_creation():
    resources = [create_test_resource()]
    collection = MyServiceResourceCollection(
        resources=resources,
        source_connector="my_service",
        total_count=len(resources),
        fetched_at=datetime.now()
    )
    
    assert len(collection.resources) == 1
    assert collection.total_count == 1
```

## Error Handling

The framework provides comprehensive error handling:
- **Validation Errors**: Pydantic validates all field types automatically
- **Missing Fields**: Clear error messages for required fields
- **Type Mismatches**: Automatic type conversion where possible
- **Model Generation**: Errors in YAML structure are caught during startup

This YAML-driven approach ensures consistent, type-safe resource definitions while maintaining flexibility for different data sources and structures. 