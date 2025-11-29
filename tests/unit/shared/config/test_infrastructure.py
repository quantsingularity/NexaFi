import os
from unittest.mock import patch
import pytest


# Assuming this is the path to your actual configuration class
# For this example, we'll use a simple mock class for demonstration
class InfrastructureConfig:
    """Simulates the class being tested."""

    def __init__(self):
        # The real class would read these from os.environ
        self.redis_host = os.environ.get("REDIS_HOST", "default_host")
        self.redis_port = int(os.environ.get("REDIS_PORT", "6379"))


# --- The actual test class ---


class TestInfrastructureConfig:

    # The patch decorator temporarily sets these environment variables
    # for the duration of this specific test method.
    @patch.dict(
        os.environ,
        {
            "REDIS_HOST": "test_redis_host",
            "REDIS_PORT": "6380",  # Added a second config value
            # You would add other relevant environment variables here
        },
    )
    def test_infrastructure_config_loads_from_env(self):
        """
        Test that InfrastructureConfig correctly loads values
        from environment variables when they are set.
        """
        # 1. Arrange/Act: Instantiate the configuration class
        # This instance should load the values defined in the @patch.dict decorator
        config = InfrastructureConfig()

        # 2. Assert: Check if the instance attributes match the patched values
        assert config.redis_host == "test_redis_host"
        assert config.redis_port == 6380  # Check the type conversion for port

        # Assert that the actual os.environ reflects the patch (optional but good for debugging)
        assert os.environ["REDIS_HOST"] == "test_redis_host"
        assert os.environ["REDIS_PORT"] == "6380"
