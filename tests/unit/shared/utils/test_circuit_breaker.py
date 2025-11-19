
import time
from unittest.mock import MagicMock, patch

import pytest

from NexaFi.backend.shared.config.infrastructure import InfrastructureConfig
from NexaFi.backend.shared.utils.circuit_breaker import (CircuitBreaker,
                                                         CircuitState,
                                                         circuit_breaker)


@pytest.fixture
def default_circuit_breaker():
    with (patch.object(InfrastructureConfig, 'CIRCUIT_BREAKER_FAILURE_THRESHOLD', 3),
          patch.object(InfrastructureConfig, 'CIRCUIT_BREAKER_RECOVERY_TIMEOUT', 5)):
        yield CircuitBreaker()

class TestCircuitBreaker:

    def test_initial_state(self, default_circuit_breaker):
        assert default_circuit_breaker.state == CircuitState.CLOSED
        assert default_circuit_breaker.failure_count == 0
        assert default_circuit_breaker.last_failure_time is None

    def test_closed_to_open_transition(self, default_circuit_breaker):
        mock_func = MagicMock(side_effect=Exception(\'Test Exception\'))

        for _ in range(default_circuit_breaker.failure_threshold - 1):
            with pytest.raises(Exception):
                default_circuit_breaker.call(mock_func)
            assert default_circuit_breaker.state == CircuitState.CLOSED

        with pytest.raises(Exception):
            default_circuit_breaker.call(mock_func)
        assert default_circuit_breaker.state == CircuitState.OPEN
        assert default_circuit_breaker.last_failure_time is not None

    def test_open_to_half_open_transition(self, default_circuit_breaker):
        mock_func = MagicMock(side_effect=Exception(\'Test Exception\'))

        # Force circuit to open
        for _ in range(default_circuit_breaker.failure_threshold):
            with pytest.raises(Exception):
                default_circuit_breaker.call(mock_func)
        assert default_circuit_breaker.state == CircuitState.OPEN

        # Advance time beyond recovery timeout
        with patch(\'time.time\', return_value=time.time() + default_circuit_breaker.recovery_timeout + 1):
            with pytest.raises(Exception): # Still raises because it's in half-open and the call fails
                default_circuit_breaker.call(mock_func)
            assert default_circuit_breaker.state == CircuitState.HALF_OPEN

    def test_half_open_to_closed_on_success(self, default_circuit_breaker):
        mock_func_fail = MagicMock(side_effect=Exception(\'Test Exception\'))
        mock_func_success = MagicMock(return_value=\'Success\')

        # Force circuit to open
        for _ in range(default_circuit_breaker.failure_threshold):
            with pytest.raises(Exception):
                default_circuit_breaker.call(mock_func_fail)

        # Advance time and make a successful call in half-open state
        with patch(\'time.time\', return_value=time.time() + default_circuit_breaker.recovery_timeout + 1):
            result = default_circuit_breaker.call(mock_func_success)
            assert result == \'Success\'
            assert default_circuit_breaker.state == CircuitState.CLOSED
            assert default_circuit_breaker.failure_count == 0

    def test_half_open_to_open_on_failure(self, default_circuit_breaker):
        mock_func_fail = MagicMock(side_effect=Exception(\'Test Exception\'))

        # Force circuit to open
        for _ in range(default_circuit_breaker.failure_threshold):
            with pytest.raises(Exception):
                default_circuit_breaker.call(mock_func_fail)

        # Advance time and make a failing call in half-open state
        with patch(\'time.time\', return_value=time.time() + default_circuit_breaker.recovery_timeout + 1):
            with pytest.raises(Exception):
                default_circuit_breaker.call(mock_func_fail)
            assert default_circuit_breaker.state == CircuitState.OPEN

    def test_call_in_open_state_raises_exception(self, default_circuit_breaker):
        mock_func = MagicMock(side_effect=Exception(\'Test Exception\'))

        # Force circuit to open
        for _ in range(default_circuit_breaker.failure_threshold):
            with pytest.raises(Exception):
                default_circuit_breaker.call(mock_func)

        # Attempt call immediately after opening
        with pytest.raises(Exception, match=\'Circuit breaker is OPEN\'):
            default_circuit_breaker.call(mock_func)

class TestCircuitBreakerDecorator:

    def test_decorator_closed_state(self):
        @circuit_breaker(failure_threshold=1, recovery_timeout=1)
        def test_func():
            return \'Success\'

        result = test_func()
        assert result == \'Success\'

    def test_decorator_open_state(self):
        @circuit_breaker(failure_threshold=1, recovery_timeout=1)
        def test_func_fail():
            raise Exception(\'Decorator Test Exception\')

        with pytest.raises(Exception):
            test_func_fail() # First call fails, opens circuit

        with pytest.raises(Exception, match=\'Circuit breaker is OPEN\'):
            test_func_fail() # Second call, circuit is open

    def test_decorator_half_open_state(self):
        breaker_instance = CircuitBreaker(failure_threshold=1, recovery_timeout=1)

        @circuit_breaker(failure_threshold=1, recovery_timeout=1)
        def test_func_half_open():
            if test_func_half_open.call_count == 0:
                test_func_half_open.call_count += 1
                raise Exception(\'First Fail\')
            else:
                return \'Success\'
        test_func_half_open.call_count = 0

        with pytest.raises(Exception): # First call fails, opens circuit
            test_func_half_open()

        # Advance time to half-open state
        with patch(\'time.time\', return_value=time.time() + 2):
            result = test_func_half_open()
            assert result == \'Success\'
