"""Mock GitHub provider for testing."""
from con_mon_v2.resources import ResourceCollection


class MockGitHubProvider:
    """Mock GitHub provider class."""
    _is_provider = True  # Required for provider detection

    def __init__(self, metadata: dict):
        """Initialize with metadata."""
        self.metadata = metadata

    def process(self) -> ResourceCollection:
        """Mock process method."""
        return ResourceCollection(resources=[]) 