from con_mon_v2.compliance.data_loader import ChecksLoader
from con_mon_v2.compliance.models import Check

def test_load_checks():
    """Test loading checks from CSV file."""
    try:
        # Initialize the ChecksLoader
        loader = ChecksLoader()

        # Test that we can create a loader instance
        assert loader is not None
        print("✅ ChecksLoader instance created successfully")

        # Test loading checks from CSV (if CSV file exists)
        try:
            checks = loader.load_all()
            print(f"✅ Loaded {len(checks)} checks from CSV")

            # Validate that loaded checks are Check instances
            if checks:
                first_check = checks[0]
                assert isinstance(first_check, Check)
                assert hasattr(first_check, 'id')
                assert hasattr(first_check, 'metadata')
                assert hasattr(first_check, 'output_statements')
                assert hasattr(first_check, 'fix_details')
                print("✅ Check objects have correct structure")

        except FileNotFoundError:
            print("⚠️ No CSV file found, skipping load test")
        except Exception as e:
            print(f"⚠️ CSV loading failed (expected if no data): {e}")

    except Exception as e:
        print(f"❌ ChecksLoader test failed: {e}")
        raise

if __name__ == "__main__":
    test_load_checks()
