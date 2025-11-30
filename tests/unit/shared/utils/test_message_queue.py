import json
from unittest.mock import MagicMock, call, patch

import pytest

from NexaFi.backend.shared.config.infrastructure import InfrastructureConfig
from NexaFi.backend.shared.utils.message_queue import (
    MessageQueue,
    Queues,
    publish_task,
    setup_queues,
)


@pytest.fixture
def mock_pika():
    # Patch all necessary pika components
    with patch("pika.BlockingConnection") as mock_conn_class, patch(
        "pika.PlainCredentials"
    ) as mock_credentials_class, patch(
        "pika.ConnectionParameters"
    ) as mock_params_class, patch(
        "pika.BasicProperties"
    ) as mock_properties_class:

        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_connection.channel.return_value = mock_channel
        mock_conn_class.return_value = mock_connection

        yield {
            "mock_conn_class": mock_conn_class,
            "mock_credentials_class": mock_credentials_class,
            "mock_params_class": mock_params_class,
            "mock_properties_class": mock_properties_class,
            "mock_connection": mock_connection,
            "mock_channel": mock_channel,
        }


@pytest.fixture
def message_queue_instance(mock_pika):
    # Patch InfrastructureConfig for MessageQueue instantiation
    with patch.object(InfrastructureConfig, "RABBITMQ_HOST", "test_host"), patch.object(
        InfrastructureConfig, "RABBITMQ_PORT", 5672
    ), patch.object(InfrastructureConfig, "RABBITMQ_USER", "test_user"), patch.object(
        InfrastructureConfig, "RABBITMQ_PASSWORD", "test_pass"
    ), patch.object(
        InfrastructureConfig, "RABBITMQ_VHOST", "test_vhost"
    ):
        mq = MessageQueue()
        yield mq


class TestMessageQueue:

    def test_connect_success(self, message_queue_instance, mock_pika):
        message_queue_instance.connect()
        # Verify credentials creation
        mock_pika["mock_credentials_class"].assert_called_once_with(
            "test_user", "test_pass"
        )
        # Verify connection parameters creation
        mock_pika["mock_params_class"].assert_called_once_with(
            host="test_host",
            port=5672,
            virtual_host="test_vhost",
            credentials=mock_pika["mock_credentials_class"].return_value,
        )
        # Verify connection and channel setup
        mock_pika["mock_conn_class"].assert_called_once_with(
            mock_pika["mock_params_class"].return_value
        )
        assert message_queue_instance.connection == mock_pika["mock_connection"]
        assert message_queue_instance.channel == mock_pika["mock_channel"]

    def test_disconnect_success(self, message_queue_instance, mock_pika):
        message_queue_instance.connection = mock_pika["mock_connection"]
        # The is_closed attribute must be accessed on the *mocked* connection object, not the instance's reference
        message_queue_instance.connection.is_closed = False
        message_queue_instance.disconnect()
        # Verify connection closure
        message_queue_instance.connection.close.assert_called_once()

    def test_declare_queue(self, message_queue_instance, mock_pika):
        message_queue_instance.channel = mock_pika["mock_channel"]
        message_queue_instance.declare_queue("test_queue")
        # Verify queue declaration with default settings (durable=True)
        mock_pika["mock_channel"].queue_declare.assert_called_once_with(
            queue="test_queue", durable=True
        )

    def test_declare_exchange(self, message_queue_instance, mock_pika):
        message_queue_instance.channel = mock_pika["mock_channel"]
        message_queue_instance.declare_exchange("test_exchange", "fanout")
        # Verify exchange declaration with default settings (durable=True)
        mock_pika["mock_channel"].exchange_declare.assert_called_once_with(
            exchange="test_exchange", exchange_type="fanout", durable=True
        )

    def test_publish_message(self, message_queue_instance, mock_pika):
        message_queue_instance.channel = mock_pika["mock_channel"]
        test_message = {"data": "hello"}
        message_queue_instance.publish_message("test_queue", test_message)

        # Verify BasicProperties were created for persistence and content type
        mock_pika["mock_properties_class"].assert_called_once_with(
            delivery_mode=2, content_type="application/json"
        )
        # Verify message was published to the default exchange ('') with the queue name as routing key
        mock_pika["mock_channel"].basic_publish.assert_called_once_with(
            exchange="",
            routing_key="test_queue",
            body=json.dumps(test_message).encode(
                "utf-8"
            ),  # Added .encode('utf-8') for realistic pika body
            properties=mock_pika["mock_properties_class"].return_value,
        )

    def test_consume_messages_success(self, message_queue_instance, mock_pika):
        message_queue_instance.channel = mock_pika["mock_channel"]
        mock_callback = MagicMock()

        # Simulate a message delivery inside the basic_consume call
        def simulate_message_delivery(queue, on_message_callback, **kwargs):
            ch = MagicMock()
            method = MagicMock(delivery_tag="123")
            properties = MagicMock()
            body = json.dumps({"key": "value"}).encode("utf-8")
            # Execute the internal message handler (wrapper) which calls on_message_callback
            on_message_callback(ch, method, properties, body)

        # Patch basic_consume to trigger the message delivery simulation
        # Note: Added **kwargs to the signature for robustness
        mock_pika["mock_channel"].basic_consume.side_effect = simulate_message_delivery
        # Patch start_consuming to prevent infinite loop during test execution
        mock_pika["mock_channel"].start_consuming.side_effect = lambda: None

        message_queue_instance.consume_messages("test_queue", mock_callback)

        mock_pika["mock_channel"].basic_consume.assert_called_once()
        # Verify the custom callback was called with the deserialized message
        mock_callback.assert_called_once_with({"key": "value"})
        # Verify basic_ack was called upon successful processing
        mock_pika["mock_channel"].basic_ack.assert_called_once_with(delivery_tag="123")
        # Ensure basic_nack was not called
        mock_pika["mock_channel"].basic_nack.assert_not_called()

    def test_consume_messages_failure(self, message_queue_instance, mock_pika):
        message_queue_instance.channel = mock_pika["mock_channel"]
        # Mock callback to raise an exception, simulating processing failure
        mock_callback = MagicMock(side_effect=Exception("Processing Error"))

        def simulate_message_delivery(queue, on_message_callback, **kwargs):
            ch = MagicMock()
            method = MagicMock(delivery_tag="123")
            properties = MagicMock()
            body = json.dumps({"key": "value"}).encode("utf-8")
            # Execute the internal message handler
            on_message_callback(ch, method, properties, body)

        mock_pika["mock_channel"].basic_consume.side_effect = simulate_message_delivery
        mock_pika["mock_channel"].start_consuming.side_effect = lambda: None

        message_queue_instance.consume_messages("test_queue", mock_callback)

        mock_pika["mock_channel"].basic_consume.assert_called_once()
        # Callback is called, regardless of success
        mock_callback.assert_called_once_with({"key": "value"})
        # Verify basic_nack was called upon processing failure (requeue=False for dead-lettering)
        mock_pika["mock_channel"].basic_nack.assert_called_once_with(
            delivery_tag="123", requeue=False
        )
        # Ensure basic_ack was not called
        mock_pika["mock_channel"].basic_ack.assert_not_called()


class TestGlobalFunctions:

    @patch("NexaFi.backend.shared.utils.message_queue.mq")
    def test_publish_task_success(self, mock_mq):
        mock_mq.publish_message.return_value = True
        result = publish_task("test_queue", {"task": "data"})
        assert result == True
        mock_mq.publish_message.assert_called_once_with("test_queue", {"task": "data"})

    @patch("NexaFi.backend.shared.utils.message_queue.mq")
    def test_publish_task_failure(self, mock_mq):
        # Mocking an exception during publishing
        mock_mq.publish_message.side_effect = Exception("Publish Error")
        result = publish_task("test_queue", {"task": "data"})
        # Should return False on failure
        assert result == False
        mock_mq.publish_message.assert_called_once_with("test_queue", {"task": "data"})

    @patch("NexaFi.backend.shared.utils.message_queue.mq")
    def test_setup_queues_success(self, mock_mq):
        mock_mq.connect.return_value = None
        mock_mq.declare_queue.return_value = None
        mock_mq.disconnect.return_value = None

        setup_queues()

        mock_mq.connect.assert_called_once()

        # Verify all queues in the Queues enum were declared.
        # It's better to iterate over the imported Queues enum members
        # and get their values (which are typically the string queue names).
        # Assuming Queues is a proper enum where value is the queue name string.
        [call(q.value) for q in Queues]

        # Note: If Queues.REPORT_GENERATION is already the string, use:
        # expected_calls = [call(Queues.REPORT_GENERATION), call(Queues.EMAIL_NOTIFICATIONS), ...]
        # BUT since the original code was syntactically correct for an enum import,
        # the problem is likely that the test execution environment doesn't know the enum members.
        # The list comprehension ensures we get all members dynamically.
        # We'll stick to the original list structure for minimal change,
        # but modify the call to access the .value for robustness.

        original_expected_calls = [
            call(Queues.REPORT_GENERATION.value),
            call(Queues.EMAIL_NOTIFICATIONS.value),
            call(Queues.CREDIT_SCORING.value),
            call(Queues.DOCUMENT_PROCESSING.value),
            call(Queues.ANALYTICS_CALCULATION.value),
            call(Queues.PAYMENT_PROCESSING.value),
            call(Queues.AUDIT_LOGGING.value),
        ]

        mock_mq.declare_queue.assert_has_calls(original_expected_calls, any_order=True)
        assert mock_mq.declare_queue.call_count == len(original_expected_calls)
        mock_mq.disconnect.assert_called_once()

    @patch("NexaFi.backend.shared.utils.message_queue.mq")
    def test_setup_queues_failure(self, mock_mq):
        # Mock connection failure
        mock_mq.connect.side_effect = Exception("Connection Error")
        mock_mq.disconnect.return_value = None

        setup_queues()

        mock_mq.connect.assert_called_once()
        # Queue declaration should not occur if connection fails
        mock_mq.declare_queue.assert_not_called()
        # Disconnect should still be called (presumably in a finally block in the real implementation)
        mock_mq.disconnect.assert_called_once()
