
import os
from unittest.mock import patch

import pytest

from NexaFi.backend.shared.config.infrastructure import InfrastructureConfig


class TestInfrastructureConfig:

    @patch.dict(os.environ, {
        \"REDIS_HOST\": \"test_redis_host\",
