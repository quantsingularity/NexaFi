
import pytest
import os
from unittest.mock import patch

from NexaFi.backend.shared.config.infrastructure import InfrastructureConfig

class TestInfrastructureConfig:

    @patch.dict(os.environ, {
        \"REDIS_HOST\": \"test_redis_host\",

