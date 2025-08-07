"""Test nested field handling in YAML loader."""
from typing import List, Dict, Any
from datetime import datetime
from con_mon_v2.utils.yaml_loader import ResourceYamlMapping


def test_primitive_types():
    """Test handling of primitive field types."""
    yaml_data = {
        "test": {
            "nested_schemas": {
                "PrimitiveTypes": {
                    "name": "primitive_types",
                    "description": "Test primitive types",
                    "fields": {
                        "string_field": "string",
                        "integer_field": "integer",
                        "boolean_field": "boolean",
                        "float_field": "float",
                        "datetime_field": "datetime",
                        "number_field": "number"
                    }
                }
            }
        }
    }

    # Load schema
    mapping = ResourceYamlMapping.load_yaml(yaml_data)
    
    # Get the model class
    model_class = mapping.nested_schemas[0]
    
    # Verify field types
    annotations = model_class.__annotations__
    assert annotations['string_field'] == str
    assert annotations['integer_field'] == int
    assert annotations['boolean_field'] == bool
    assert annotations['float_field'] == float
    assert annotations['datetime_field'] == datetime
    assert annotations['number_field'] == float

    print("✅ Primitive types handled correctly")


def test_array_types():
    """Test handling of array fields."""
    yaml_data = {
        "test": {
            "nested_schemas": {
                "ArrayTypes": {
                    "name": "array_types",
                    "description": "Test array types",
                    "fields": {
                        "simple_array": "array",  # Simple string array
                        "typed_array": {  # Array with type
                            "type": "array",
                            "structure": {
                                "id": "integer",
                                "name": "string"
                            }
                        },
                        "nested_array": {  # Array with nested structure
                            "type": "array",
                            "structure": {
                                "metadata": {
                                    "type": "object",
                                    "structure": {
                                        "created_at": "datetime",
                                        "tags": "array"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    # Load schema
    mapping = ResourceYamlMapping.load_yaml(yaml_data)
    
    # Get the model class
    model_class = mapping.nested_schemas[0]
    
    # Verify field types
    annotations = model_class.__annotations__
    
    # Simple array should be List[str]
    assert annotations['simple_array'] == List[str]
    
    # Typed array should be List[BaseModel] with proper structure
    assert isinstance(annotations['typed_array'], type(List[Any]))  # Check it's a List type
    item_model = annotations['typed_array'].__args__[0]  # Get the item type
    assert hasattr(item_model, '__annotations__')  # Check it's a model
    assert item_model.__annotations__['id'] == int
    assert item_model.__annotations__['name'] == str
    
    # Nested array should have deep structure
    assert isinstance(annotations['nested_array'], type(List[Any]))  # Check it's a List type
    nested_model = annotations['nested_array'].__args__[0]  # Get the item type
    assert hasattr(nested_model, '__annotations__')  # Check it's a model
    assert 'metadata' in nested_model.__annotations__
    metadata_model = nested_model.__annotations__['metadata']
    assert metadata_model.__annotations__['created_at'] == datetime
    assert metadata_model.__annotations__['tags'] == List[str]

    print("✅ Array types handled correctly")


def test_object_types():
    """Test handling of object fields."""
    yaml_data = {
        "test": {
            "nested_schemas": {
                "ObjectTypes": {
                    "name": "object_types",
                    "description": "Test object types",
                    "fields": {
                        "simple_object": {  # Simple object
                            "type": "object",
                            "structure": {
                                "id": "integer",
                                "name": "string"
                            }
                        },
                        "nested_object": {  # Nested object
                            "type": "object",
                            "structure": {
                                "metadata": {
                                    "type": "object",
                                    "structure": {
                                        "created_at": "datetime",
                                        "updated_at": "datetime"
                                    }
                                },
                                "settings": {
                                    "type": "object",
                                    "structure": {
                                        "enabled": "boolean",
                                        "config": {
                                            "type": "object",
                                            "structure": {
                                                "timeout": "integer",
                                                "retries": "integer"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    # Load schema
    mapping = ResourceYamlMapping.load_yaml(yaml_data)
    
    # Get the model class
    model_class = mapping.nested_schemas[0]
    
    # Verify field types
    annotations = model_class.__annotations__
    
    # Simple object should be a BaseModel with proper structure
    simple_model = annotations['simple_object']
    assert simple_model.__annotations__['id'] == int
    assert simple_model.__annotations__['name'] == str
    
    # Nested object should have deep structure
    nested_model = annotations['nested_object']
    
    # Check metadata structure
    metadata_model = nested_model.__annotations__['metadata']
    assert metadata_model.__annotations__['created_at'] == datetime
    assert metadata_model.__annotations__['updated_at'] == datetime
    
    # Check settings structure
    settings_model = nested_model.__annotations__['settings']
    assert settings_model.__annotations__['enabled'] == bool
    config_model = settings_model.__annotations__['config']
    assert config_model.__annotations__['timeout'] == int
    assert config_model.__annotations__['retries'] == int

    print("✅ Object types handled correctly")


def test_model_references():
    """Test handling of model references."""
    yaml_data = {
        "test": {
            "nested_schemas": {
                "UserProfile": {  # First define a model that will be referenced
                    "name": "user_profile",
                    "description": "User profile information",
                    "fields": {
                        "username": "string",
                        "email": "string",
                        "joined_at": "datetime"
                    }
                },
                "CommentData": {  # Another referenceable model
                    "name": "comment_data",
                    "description": "Comment information",
                    "fields": {
                        "text": "string",
                        "created_at": "datetime"
                    }
                },
                "PostData": {  # Model that references others
                    "name": "post_data",
                    "description": "Post with references",
                    "fields": {
                        "title": "string",
                        "author": "UserProfile",  # Reference to UserProfile
                        "comments": {  # Array of references
                            "type": "array",
                            "structure": {
                                "comment": "CommentData",  # Reference to CommentData
                                "author": "UserProfile"  # Another reference
                            }
                        }
                    }
                }
            }
        }
    }

    # Load schema
    mapping = ResourceYamlMapping.load_yaml(yaml_data)
    
    # Get the model classes
    models = {model.__name__: model for model in mapping.nested_schemas}
    
    # Get the PostData model
    post_model = models['PostData']
    annotations = post_model.__annotations__
    
    # Verify direct reference
    assert annotations['author'] == models['UserProfile']
    
    # Verify array of references
    assert isinstance(annotations['comments'], type(List[Any]))  # Check it's a List type
    comment_item_model = annotations['comments'].__args__[0]  # Get the item type
    assert hasattr(comment_item_model, '__annotations__')  # Check it's a model
    assert comment_item_model.__annotations__['comment'] == models['CommentData']
    assert comment_item_model.__annotations__['author'] == models['UserProfile']

    print("✅ Model references handled correctly")


def test_resource_fields():
    """Test handling of resource fields."""
    yaml_data = {
        "test": {
            "nested_schemas": {
                "MetadataSchema": {
                    "name": "metadata_schema",
                    "description": "Metadata information",
                    "fields": {
                        "created_at": "datetime",
                        "tags": "array"
                    }
                }
            },
            "resources": {
                "TestResource": {
                    "name": "test",
                    "description": "Test resource",
                    "service": "test_service",
                    "fields": {
                        "id": "string",
                        "metadata": "MetadataSchema",  # Reference to schema
                        "settings": {
                            "type": "object",
                            "structure": {
                                "enabled": "boolean",
                                "config": {
                                    "type": "array",
                                    "structure": {
                                        "name": "string",
                                        "value": "string"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    # Load schema
    mapping = ResourceYamlMapping.load_yaml(yaml_data)
    
    # Get the resource model
    resource_model = mapping.resources[0]
    annotations = resource_model.__annotations__
    
    # Verify standard resource fields
    assert annotations['service'] == str
    assert annotations['name'] == str
    assert annotations['description'] == str
    
    # Verify custom fields
    assert annotations['id'] == str
    assert annotations['metadata'] == mapping.nested_schemas[0]  # Should be MetadataSchema
    
    # Verify nested settings
    settings_model = annotations['settings']
    assert settings_model.__annotations__['enabled'] == bool
    
    config_model = settings_model.__annotations__['config']
    assert isinstance(config_model, type(List[Any]))  # Check it's a List type
    config_item_model = config_model.__args__[0]  # Get the item type
    assert hasattr(config_item_model, '__annotations__')  # Check it's a model
    assert config_item_model.__annotations__['name'] == str
    assert config_item_model.__annotations__['value'] == str

    print("✅ Resource fields handled correctly")


def main():
    """Run all nested field tests."""
    print("\nTesting nested field handling...")
    
    test_primitive_types()
    test_array_types()
    test_object_types()
    test_model_references()
    test_resource_fields()
    
    print("\n✅ All nested field tests passed!")


if __name__ == "__main__":
    main() 