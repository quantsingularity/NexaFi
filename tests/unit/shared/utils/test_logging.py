
import json
import logging
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from NexaFi.backend.shared.config.infrastructure import InfrastructureConfig
from NexaFi.backend.shared.utils.logging import StructuredLogger, get_logger


@pytest.fixture
def mock_logger():
    with patch("logging.getLogger") as mock_get_logger:
        mock_instance = MagicMock()
        mock_get_logger.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_stream_handler():
    with patch("logging.StreamHandler") as mock_handler:
        mock_instance = MagicMock()
        mock_handler.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_file_handler():
    with patch("logging.FileHandler") as mock_handler:
        mock_instance = MagicMock()
        mock_handler.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def structured_logger(mock_logger, mock_stream_handler, mock_file_handler):
    with patch.object(InfrastructureConfig, \'LOG_LEVEL\', \'INFO\'), \
         patch.object(InfrastructureConfig, \'LOG_FORMAT\', \'%(message)s\'):
        logger = StructuredLogger(\'test_service\')
        yield logger

class TestStructuredLogger:

    def test_init(self, mock_logger, mock_stream_handler, mock_file_handler):
        with patch.object(InfrastructureConfig, \'LOG_LEVEL\', \'DEBUG\'), \
             patch.object(InfrastructureConfig, \'LOG_FORMAT\', \'%(asctime)s - %(message)s\'):
            logger = StructuredLogger(\'another_service\')

            mock_logger.assert_called_once_with(\'another_service\')
            mock_logger.return_value.setLevel.assert_called_once_with(logging.DEBUG)
            mock_stream_handler.assert_called_once_with()
            mock_stream_handler.return_value.setFormatter.assert_called_once()
            mock_logger.return_value.addHandler.assert_any_call(mock_stream_handler.return_value)
            mock_file_handler.assert_called_once_with(\'logs/another_service.log\')
            mock_file_handler.return_value.setFormatter.assert_called_once()
            mock_logger.return_value.addHandler.assert_any_call(mock_file_handler.return_value)

    def test_create_log_entry(self, structured_logger):
        with patch("datetime.utcnow", return_value=datetime(2024, 1, 1, 12, 0, 0)):
            entry = structured_logger._create_log_entry(\'INFO\', \'Test message\', {\'key\': \'value\'})
            assert entry[\'timestamp\'] == \'2024-01-01T12:00:00\'
            assert entry[\'service\'] == \'test_service\'
            assert entry[\'level\'] == \'INFO\'
            assert entry[\'message\'] == \'Test message\'
            assert entry[\'key\'] == \'value\'

    def test_info_logging(self, structured_logger, mock_logger):
        with patch("datetime.utcnow", return_value=datetime(2024, 1, 1, 12, 0, 0)):
            structured_logger.info(\'Info message\', user_id=\'123\')
            expected_log = {
                \'timestamp\': \'2024-01-01T12:00:00\
',
                \'service\': \'test_service\
',
                \'level\': \'INFO\
',
                \'message\': \'Info message\
',
                \'user_id\': \'123\'
            }
            mock_logger.return_value.info.assert_called_once_with(json.dumps(expected_log))

    def test_warning_logging(self, structured_logger, mock_logger):
        with patch("datetime.utcnow", return_value=datetime(2024, 1, 1, 12, 0, 0)):
            structured_logger.warning(\'Warning message\')
            expected_log = {
                \'timestamp\': \'2024-01-01T12:00:00\
',
                \'service\': \'test_service\
',
                \'level\': \'WARNING\
',
                \'message\': \'Warning message\'
            }
            mock_logger.return_value.warning.assert_called_once_with(json.dumps(expected_log))

    def test_error_logging(self, structured_logger, mock_logger):
        with patch("datetime.utcnow", return_value=datetime(2024, 1, 1, 12, 0, 0)):
            structured_logger.error(\'Error message\', error_code=500)
            expected_log = {
                \'timestamp\': \'2024-01-01T12:00:00\
',
                \'service\': \'test_service\
',
                \'level\': \'ERROR\
',
                \'message\': \'Error message\
',
                \'error_code\': 500
            }
            mock_logger.return_value.error.assert_called_once_with(json.dumps(expected_log))

    def test_debug_logging(self, structured_logger, mock_logger):
        with patch("datetime.utcnow", return_value=datetime(2024, 1, 1, 12, 0, 0)):
            structured_logger.debug(\'Debug message\')
            expected_log = {
                \'timestamp\': \'2024-01-01T12:00:00\
',
                \'service\': \'test_service\
',
                \'level\': \'DEBUG\
',
                \'message\': \'Debug message\'
            }
            mock_logger.return_value.debug.assert_called_once_with(json.dumps(expected_log))

    def test_critical_logging(self, structured_logger, mock_logger):
        with patch("datetime.utcnow", return_value=datetime(2024, 1, 1, 12, 0, 0)):
            structured_logger.critical(\'Critical message\')
            expected_log = {
                \'timestamp\': \'2024-01-01T12:00:00\
',
                \'service\': \'test_service\
',
                \'level\': \'CRITICAL\
',
                \'message\': \'Critical message\'
            }
            mock_logger.return_value.critical.assert_called_once_with(json.dumps(expected_log))

    def test_get_logger(self, mock_logger):
        with patch.object(InfrastructureConfig, \'LOG_LEVEL\', \'INFO\'), \
             patch.object(InfrastructureConfig, \'LOG_FORMAT\', \'%(message)s\'):
            logger = get_logger(\'another_service_for_get_logger\')
            assert isinstance(logger, StructuredLogger)
            mock_logger.assert_called_once_with(\'another_service_for_get_logger\')
