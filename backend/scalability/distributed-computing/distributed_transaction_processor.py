"""
Distributed Transaction Processing System for NexaFi
High-performance, scalable transaction processing with enterprise-grade reliability
"""

import hashlib
import json
import multiprocessing as mp
import time
import uuid
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

import pika
import redis
import structlog
from kafka import KafkaConsumer, KafkaProducer
from prometheus_client import Counter, Gauge, Histogram
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from tenacity import retry, stop_after_attempt, wait_exponential

Base = declarative_base()


class TransactionStatus(Enum):
    """Transaction processing status"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class Priority(Enum):
    """Transaction priority levels"""

    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BATCH = 5


@dataclass
class Transaction:
    """Transaction data structure"""

    transaction_id: str
    user_id: str
    transaction_type: str
    amount: float
    currency: str
    source_account: str
    destination_account: str
    metadata: Dict[str, Any]
    priority: Priority
    timestamp: datetime
    status: TransactionStatus
    processing_node: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: int = 30
    checksum: Optional[str] = None


@dataclass
class ProcessingResult:
    """Transaction processing result"""

    transaction_id: str
    success: bool
    status: TransactionStatus
    result_data: Dict[str, Any]
    processing_time: float
    error_message: Optional[str] = None
    node_id: str = ""


class TransactionLog(Base):
    """Transaction log model"""

    __tablename__ = "transaction_logs"

    id = Column(Integer, primary_key=True)
    transaction_id = Column(String(100), unique=True, nullable=False, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    transaction_type = Column(String(50), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), nullable=False)
    source_account = Column(String(100), nullable=False)
    destination_account = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False, index=True)
    priority = Column(Integer, nullable=False)
    processing_node = Column(String(100))
    retry_count = Column(Integer, default=0)
    metadata = Column(Text)  # JSON
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)
    processing_time = Column(Float)
    error_message = Column(Text)
    checksum = Column(String(256))


class NodeMetrics(Base):
    """Processing node metrics"""

    __tablename__ = "node_metrics"

    id = Column(Integer, primary_key=True)
    node_id = Column(String(100), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    cpu_usage = Column(Float)
    memory_usage = Column(Float)
    disk_usage = Column(Float)
    network_io = Column(Float)
    active_transactions = Column(Integer)
    completed_transactions = Column(Integer)
    failed_transactions = Column(Integer)
    avg_processing_time = Column(Float)
    queue_size = Column(Integer)
    is_healthy = Column(Boolean, default=True)


# Add indexes for performance
Index("idx_transaction_status_priority", TransactionLog.status, TransactionLog.priority)
Index(
    "idx_transaction_created_status", TransactionLog.created_at, TransactionLog.status
)
Index("idx_node_timestamp", NodeMetrics.timestamp)


class MessageQueue:
    """Distributed message queue abstraction"""

    def __init__(self, queue_type: str = "redis", config: Dict[str, Any] = None):
        self.queue_type = queue_type
        self.config = config or {}
        self.logger = structlog.get_logger(__name__)
        self._initialize_queue()

    def _initialize_queue(self):
        """Initialize message queue based on type"""
        if self.queue_type == "redis":
            self.redis_client = redis.from_url(
                self.config.get("redis_url", "redis://localhost:6379/0"),
                decode_responses=True,
            )
        elif self.queue_type == "rabbitmq":
            self.connection = pika.BlockingConnection(
                pika.URLParameters(self.config.get("rabbitmq_url", "amqp://localhost"))
            )
            self.channel = self.connection.channel()
        elif self.queue_type == "kafka":
            self.producer = KafkaProducer(
                bootstrap_servers=self.config.get("kafka_servers", ["localhost:9092"]),
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
        else:
            raise ValueError(f"Unsupported queue type: {self.queue_type}")

    def publish(self, queue_name: str, message: Dict[str, Any], priority: int = 0):
        """Publish message to queue"""
        try:
            if self.queue_type == "redis":
                # Use Redis sorted sets for priority queues
                score = priority + time.time() / 1000000  # Ensure FIFO within priority
                self.redis_client.zadd(queue_name, {json.dumps(message): score})

            elif self.queue_type == "rabbitmq":
                self.channel.queue_declare(queue=queue_name, durable=True)
                self.channel.basic_publish(
                    exchange="",
                    routing_key=queue_name,
                    body=json.dumps(message),
                    properties=pika.BasicProperties(
                        delivery_mode=2, priority=priority  # Make message persistent
                    ),
                )

            elif self.queue_type == "kafka":
                self.producer.send(queue_name, message)
                self.producer.flush()

        except Exception as e:
            self.logger.error(f"Failed to publish message: {str(e)}")
            raise

    def consume(self, queue_name: str, timeout: int = 1) -> Optional[Dict[str, Any]]:
        """Consume message from queue"""
        try:
            if self.queue_type == "redis":
                # Get highest priority message
                result = self.redis_client.zpopmin(queue_name, count=1)
                if result:
                    message_json, _ = result[0]
                    return json.loads(message_json)
                return None

            elif self.queue_type == "rabbitmq":
                method, properties, body = self.channel.basic_get(
                    queue=queue_name, auto_ack=True
                )
                if body:
                    return json.loads(body.decode("utf-8"))
                return None

            elif self.queue_type == "kafka":
                consumer = KafkaConsumer(
                    queue_name,
                    bootstrap_servers=self.config.get(
                        "kafka_servers", ["localhost:9092"]
                    ),
                    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                    consumer_timeout_ms=timeout * 1000,
                )

                for message in consumer:
                    consumer.close()
                    return message.value

                consumer.close()
                return None

        except Exception as e:
            self.logger.error(f"Failed to consume message: {str(e)}")
            return None

    def get_queue_size(self, queue_name: str) -> int:
        """Get queue size"""
        try:
            if self.queue_type == "redis":
                return self.redis_client.zcard(queue_name)
            elif self.queue_type == "rabbitmq":
                method = self.channel.queue_declare(queue=queue_name, passive=True)
                return method.method.message_count
            elif self.queue_type == "kafka":
                # Kafka doesn't provide direct queue size, return 0
                return 0
        except Exception:
            return 0


class LoadBalancer:
    """Intelligent load balancer for transaction distribution"""

    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
        self.logger = structlog.get_logger(__name__)
        self.nodes = {}
        self.load_balancing_strategy = "weighted_round_robin"

    def register_node(self, node_id: str, capacity: int, capabilities: List[str]):
        """Register processing node"""
        node_info = {
            "node_id": node_id,
            "capacity": capacity,
            "capabilities": capabilities,
            "current_load": 0,
            "last_heartbeat": time.time(),
            "is_healthy": True,
        }

        self.nodes[node_id] = node_info
        self.redis_client.hset("processing_nodes", node_id, json.dumps(node_info))

        self.logger.info(f"Registered processing node: {node_id}")

    def update_node_load(self, node_id: str, current_load: int):
        """Update node load information"""
        if node_id in self.nodes:
            self.nodes[node_id]["current_load"] = current_load
            self.nodes[node_id]["last_heartbeat"] = time.time()

            # Update in Redis
            self.redis_client.hset(
                "processing_nodes", node_id, json.dumps(self.nodes[node_id])
            )

    def select_node(self, transaction: Transaction) -> Optional[str]:
        """Select best node for transaction processing"""
        try:
            available_nodes = self._get_healthy_nodes()

            if not available_nodes:
                return None

            if self.load_balancing_strategy == "round_robin":
                return self._round_robin_selection(available_nodes)
            elif self.load_balancing_strategy == "weighted_round_robin":
                return self._weighted_round_robin_selection(available_nodes)
            elif self.load_balancing_strategy == "least_connections":
                return self._least_connections_selection(available_nodes)
            elif self.load_balancing_strategy == "capability_based":
                return self._capability_based_selection(available_nodes, transaction)
            else:
                return available_nodes[0]["node_id"]  # Default to first available

        except Exception as e:
            self.logger.error(f"Node selection failed: {str(e)}")
            return None

    def _get_healthy_nodes(self) -> List[Dict[str, Any]]:
        """Get list of healthy nodes"""
        healthy_nodes = []
        current_time = time.time()

        for node_id, node_info in self.nodes.items():
            # Check if node is healthy and recently active
            if (
                node_info["is_healthy"]
                and current_time - node_info["last_heartbeat"]
                < 60  # 60 seconds timeout
                and node_info["current_load"] < node_info["capacity"]
            ):
                healthy_nodes.append(node_info)

        return healthy_nodes

    def _round_robin_selection(self, nodes: List[Dict[str, Any]]) -> str:
        """Round robin node selection"""
        # Simple round robin based on Redis counter
        counter = self.redis_client.incr("round_robin_counter")
        selected_node = nodes[(counter - 1) % len(nodes)]
        return selected_node["node_id"]

    def _weighted_round_robin_selection(self, nodes: List[Dict[str, Any]]) -> str:
        """Weighted round robin based on node capacity"""
        # Calculate weights based on available capacity
        weights = []
        for node in nodes:
            available_capacity = node["capacity"] - node["current_load"]
            weights.append(max(1, available_capacity))  # Minimum weight of 1

        # Weighted selection
        total_weight = sum(weights)
        counter = self.redis_client.incr("weighted_rr_counter")

        cumulative_weight = 0
        target = (counter - 1) % total_weight

        for i, weight in enumerate(weights):
            cumulative_weight += weight
            if target < cumulative_weight:
                return nodes[i]["node_id"]

        return nodes[0]["node_id"]  # Fallback

    def _least_connections_selection(self, nodes: List[Dict[str, Any]]) -> str:
        """Select node with least current load"""
        min_load_node = min(nodes, key=lambda n: n["current_load"])
        return min_load_node["node_id"]

    def _capability_based_selection(
        self, nodes: List[Dict[str, Any]], transaction: Transaction
    ) -> str:
        """Select node based on transaction requirements and node capabilities"""
        # Filter nodes by required capabilities
        required_capabilities = transaction.metadata.get("required_capabilities", [])

        if required_capabilities:
            capable_nodes = [
                node
                for node in nodes
                if all(cap in node["capabilities"] for cap in required_capabilities)
            ]

            if capable_nodes:
                nodes = capable_nodes

        # Among capable nodes, select least loaded
        return self._least_connections_selection(nodes)


class TransactionProcessor:
    """Individual transaction processor"""

    def __init__(self, node_id: str, db_session, redis_client: redis.Redis):
        self.node_id = node_id
        self.db_session = db_session
        self.redis_client = redis_client
        self.logger = structlog.get_logger(__name__)
        self.is_running = False
        self.current_transactions = {}

        # Metrics
        self.processed_counter = Counter(
            "transactions_processed_total",
            "Total processed transactions",
            ["node", "status"],
        )
        self.processing_time = Histogram(
            "transaction_processing_seconds",
            "Transaction processing time",
            ["node", "type"],
        )
        self.active_transactions = Gauge(
            "active_transactions", "Currently active transactions", ["node"]
        )

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def process_transaction(self, transaction: Transaction) -> ProcessingResult:
        """Process a single transaction"""
        start_time = time.time()

        try:
            self.logger.info(f"Processing transaction {transaction.transaction_id}")

            # Validate transaction
            if not self._validate_transaction(transaction):
                raise ValueError("Transaction validation failed")

            # Update transaction status
            self._update_transaction_status(transaction, TransactionStatus.PROCESSING)

            # Add to active transactions
            self.current_transactions[transaction.transaction_id] = transaction
            self.active_transactions.labels(node=self.node_id).inc()

            # Process based on transaction type
            result_data = self._execute_transaction_logic(transaction)

            # Complete transaction
            processing_time = time.time() - start_time
            self._update_transaction_status(
                transaction, TransactionStatus.COMPLETED, processing_time
            )

            # Update metrics
            self.processed_counter.labels(node=self.node_id, status="completed").inc()
            self.processing_time.labels(
                node=self.node_id, type=transaction.transaction_type
            ).observe(processing_time)

            return ProcessingResult(
                transaction_id=transaction.transaction_id,
                success=True,
                status=TransactionStatus.COMPLETED,
                result_data=result_data,
                processing_time=processing_time,
                node_id=self.node_id,
            )

        except Exception as e:
            processing_time = time.time() - start_time
            error_message = str(e)

            self.logger.error(f"Transaction processing failed: {error_message}")

            # Update transaction status
            self._update_transaction_status(
                transaction, TransactionStatus.FAILED, processing_time, error_message
            )

            # Update metrics
            self.processed_counter.labels(node=self.node_id, status="failed").inc()

            return ProcessingResult(
                transaction_id=transaction.transaction_id,
                success=False,
                status=TransactionStatus.FAILED,
                result_data={},
                processing_time=processing_time,
                error_message=error_message,
                node_id=self.node_id,
            )

        finally:
            # Remove from active transactions
            if transaction.transaction_id in self.current_transactions:
                del self.current_transactions[transaction.transaction_id]
                self.active_transactions.labels(node=self.node_id).dec()

    def _validate_transaction(self, transaction: Transaction) -> bool:
        """Validate transaction data"""
        try:
            # Basic validation
            if not transaction.transaction_id or not transaction.user_id:
                return False

            if transaction.amount <= 0:
                return False

            if not transaction.source_account or not transaction.destination_account:
                return False

            # Verify checksum if present
            if transaction.checksum:
                calculated_checksum = self._calculate_checksum(transaction)
                if calculated_checksum != transaction.checksum:
                    return False

            # Business logic validation
            if not self._validate_business_rules(transaction):
                return False

            return True

        except Exception as e:
            self.logger.error(f"Transaction validation error: {str(e)}")
            return False

    def _calculate_checksum(self, transaction: Transaction) -> str:
        """Calculate transaction checksum"""
        data = f"{transaction.transaction_id}{transaction.user_id}{transaction.amount}{transaction.currency}{transaction.source_account}{transaction.destination_account}"
        return hashlib.sha256(data.encode()).hexdigest()

    def _validate_business_rules(self, transaction: Transaction) -> bool:
        """Validate business rules"""
        try:
            # Check account balances
            if not self._check_account_balance(
                transaction.source_account, transaction.amount
            ):
                return False

            # Check transaction limits
            if not self._check_transaction_limits(transaction):
                return False

            # Check compliance rules
            if not self._check_compliance_rules(transaction):
                return False

            return True

        except Exception as e:
            self.logger.error(f"Business rule validation error: {str(e)}")
            return False

    def _check_account_balance(self, account_id: str, amount: float) -> bool:
        """Check if account has sufficient balance"""
        try:
            # This would integrate with account management system
            # For now, simulate balance check
            cache_key = f"account_balance:{account_id}"
            balance = self.redis_client.get(cache_key)

            if balance:
                return float(balance) >= amount

            # If not in cache, assume sufficient balance for demo
            return True

        except Exception:
            return False

    def _check_transaction_limits(self, transaction: Transaction) -> bool:
        """Check transaction limits"""
        try:
            # Daily limit check
            daily_limit_key = f"daily_limit:{transaction.user_id}:{datetime.now().strftime('%Y-%m-%d')}"
            daily_total = self.redis_client.get(daily_limit_key)

            if (
                daily_total and float(daily_total) + transaction.amount > 100000
            ):  # $100k daily limit
                return False

            # Single transaction limit
            if transaction.amount > 50000:  # $50k single transaction limit
                return False

            return True

        except Exception:
            return False

    def _check_compliance_rules(self, transaction: Transaction) -> bool:
        """Check compliance and regulatory rules"""
        try:
            # AML checks
            if transaction.amount > 10000:  # Large transaction reporting threshold
                # Would integrate with AML system
                pass

            # Sanctions screening
            # Would integrate with sanctions screening system

            # KYC verification
            # Would verify customer identity

            return True

        except Exception:
            return False

    def _execute_transaction_logic(self, transaction: Transaction) -> Dict[str, Any]:
        """Execute transaction-specific logic"""
        try:
            if transaction.transaction_type == "transfer":
                return self._process_transfer(transaction)
            elif transaction.transaction_type == "payment":
                return self._process_payment(transaction)
            elif transaction.transaction_type == "withdrawal":
                return self._process_withdrawal(transaction)
            elif transaction.transaction_type == "deposit":
                return self._process_deposit(transaction)
            else:
                raise ValueError(
                    f"Unknown transaction type: {transaction.transaction_type}"
                )

        except Exception as e:
            self.logger.error(f"Transaction execution error: {str(e)}")
            raise

    def _process_transfer(self, transaction: Transaction) -> Dict[str, Any]:
        """Process money transfer"""
        # Simulate transfer processing
        time.sleep(0.1)  # Simulate processing time

        # Debit source account
        self._update_account_balance(transaction.source_account, -transaction.amount)

        # Credit destination account
        self._update_account_balance(
            transaction.destination_account, transaction.amount
        )

        # Update daily limits
        daily_limit_key = (
            f"daily_limit:{transaction.user_id}:{datetime.now().strftime('%Y-%m-%d')}"
        )
        self.redis_client.incrbyfloat(daily_limit_key, transaction.amount)
        self.redis_client.expire(daily_limit_key, 86400)  # 24 hours

        return {
            "transfer_id": str(uuid.uuid4()),
            "source_balance": self._get_account_balance(transaction.source_account),
            "destination_balance": self._get_account_balance(
                transaction.destination_account
            ),
            "exchange_rate": 1.0,  # Simplified
            "fees": 0.0,  # Simplified
        }

    def _process_payment(self, transaction: Transaction) -> Dict[str, Any]:
        """Process payment"""
        # Similar to transfer but with payment-specific logic
        time.sleep(0.05)

        # Process payment
        self._update_account_balance(transaction.source_account, -transaction.amount)

        return {
            "payment_id": str(uuid.uuid4()),
            "merchant_id": transaction.destination_account,
            "authorization_code": f"AUTH{int(time.time())}",
            "fees": transaction.amount * 0.029,  # 2.9% fee
        }

    def _process_withdrawal(self, transaction: Transaction) -> Dict[str, Any]:
        """Process withdrawal"""
        time.sleep(0.08)

        # Process withdrawal
        self._update_account_balance(transaction.source_account, -transaction.amount)

        return {
            "withdrawal_id": str(uuid.uuid4()),
            "atm_id": transaction.metadata.get("atm_id", "ATM001"),
            "cash_dispensed": transaction.amount,
        }

    def _process_deposit(self, transaction: Transaction) -> Dict[str, Any]:
        """Process deposit"""
        time.sleep(0.03)

        # Process deposit
        self._update_account_balance(
            transaction.destination_account, transaction.amount
        )

        return {
            "deposit_id": str(uuid.uuid4()),
            "deposit_method": transaction.metadata.get(
                "deposit_method", "bank_transfer"
            ),
            "clearing_time": "immediate",
        }

    def _update_account_balance(self, account_id: str, amount: float):
        """Update account balance"""
        cache_key = f"account_balance:{account_id}"
        self.redis_client.incrbyfloat(cache_key, amount)

    def _get_account_balance(self, account_id: str) -> float:
        """Get account balance"""
        cache_key = f"account_balance:{account_id}"
        balance = self.redis_client.get(cache_key)
        return float(balance) if balance else 0.0

    def _update_transaction_status(
        self,
        transaction: Transaction,
        status: TransactionStatus,
        processing_time: float = None,
        error_message: str = None,
    ):
        """Update transaction status in database"""
        try:
            # Update in database
            tx_log = (
                self.db_session.query(TransactionLog)
                .filter_by(transaction_id=transaction.transaction_id)
                .first()
            )

            if tx_log:
                tx_log.status = status.value
                tx_log.processing_node = self.node_id
                tx_log.updated_at = datetime.utcnow()

                if status == TransactionStatus.COMPLETED:
                    tx_log.completed_at = datetime.utcnow()

                if processing_time is not None:
                    tx_log.processing_time = processing_time

                if error_message:
                    tx_log.error_message = error_message

                self.db_session.commit()

            # Update in Redis for real-time status
            status_key = f"transaction_status:{transaction.transaction_id}"
            status_data = {
                "status": status.value,
                "processing_node": self.node_id,
                "updated_at": datetime.utcnow().isoformat(),
            }

            if error_message:
                status_data["error_message"] = error_message

            self.redis_client.setex(
                status_key, 3600, json.dumps(status_data)
            )  # 1 hour TTL

        except Exception as e:
            self.logger.error(f"Status update failed: {str(e)}")


class DistributedTransactionManager:
    """Main distributed transaction management system"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = structlog.get_logger(__name__)

        # Initialize components
        self.message_queue = MessageQueue(
            queue_type=config.get("queue_type", "redis"),
            config=config.get("queue_config", {}),
        )

        # Initialize database
        self.db_engine = create_engine(
            config.get("database_url", "postgresql://localhost/nexafi"),
            poolclass=QueuePool,
            pool_size=20,
            max_overflow=30,
            pool_pre_ping=True,
        )

        Session = sessionmaker(bind=self.db_engine)
        self.db_session = Session()

        # Initialize Redis
        self.redis_client = redis.from_url(
            config.get("redis_url", "redis://localhost:6379/0"),
            decode_responses=True,
            connection_pool_kwargs={"max_connections": 50},
        )

        # Initialize load balancer
        self.load_balancer = LoadBalancer(self.redis_client)

        # Initialize processors
        self.processors = {}
        self.is_running = False

        # Create database tables
        Base.metadata.create_all(bind=self.db_engine)

        # Metrics
        self.submitted_counter = Counter(
            "transactions_submitted_total", "Total submitted transactions"
        )
        self.queue_size_gauge = Gauge(
            "transaction_queue_size", "Transaction queue size", ["priority"]
        )
        self.throughput_gauge = Gauge(
            "transaction_throughput", "Transaction throughput per second"
        )

    def start_processing(self, num_workers: int = None):
        """Start distributed transaction processing"""
        if self.is_running:
            return

        self.is_running = True

        # Determine number of workers
        if num_workers is None:
            num_workers = min(mp.cpu_count() * 2, 16)  # Max 16 workers

        self.logger.info(f"Starting {num_workers} transaction processors")

        # Start worker processes
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            futures = []

            for i in range(num_workers):
                node_id = f"processor_{i}_{int(time.time())}"

                # Register node with load balancer
                self.load_balancer.register_node(
                    node_id=node_id,
                    capacity=100,  # Max concurrent transactions
                    capabilities=["transfer", "payment", "withdrawal", "deposit"],
                )

                # Start processor
                future = executor.submit(self._run_processor, node_id)
                futures.append(future)

            # Wait for all processors to complete
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    self.logger.error(f"Processor failed: {str(e)}")

    def _run_processor(self, node_id: str):
        """Run individual transaction processor"""
        try:
            processor = TransactionProcessor(
                node_id, self.db_session, self.redis_client
            )

            self.logger.info(f"Started processor: {node_id}")

            while self.is_running:
                try:
                    # Get transaction from queue
                    message = self.message_queue.consume("transaction_queue", timeout=1)

                    if message:
                        # Deserialize transaction
                        transaction = Transaction(**message)

                        # Process transaction
                        result = processor.process_transaction(transaction)

                        # Update load balancer
                        current_load = len(processor.current_transactions)
                        self.load_balancer.update_node_load(node_id, current_load)

                        self.logger.info(
                            f"Processed transaction {transaction.transaction_id}: {result.status.value}"
                        )

                    else:
                        # No transactions available, brief sleep
                        time.sleep(0.1)

                except Exception as e:
                    self.logger.error(f"Processing error in {node_id}: {str(e)}")
                    time.sleep(1)  # Brief pause on error

        except Exception as e:
            self.logger.error(f"Processor {node_id} failed: {str(e)}")

    def submit_transaction(self, transaction: Transaction) -> str:
        """Submit transaction for processing"""
        try:
            # Generate transaction ID if not provided
            if not transaction.transaction_id:
                transaction.transaction_id = str(uuid.uuid4())

            # Calculate checksum
            transaction.checksum = self._calculate_checksum(transaction)

            # Store in database
            self._store_transaction(transaction)

            # Submit to queue
            message = asdict(transaction)

            # Convert datetime to string for JSON serialization
            message["timestamp"] = transaction.timestamp.isoformat()
            message["status"] = transaction.status.value
            message["priority"] = transaction.priority.value

            # Determine queue priority
            priority = transaction.priority.value

            # Submit to message queue
            self.message_queue.publish("transaction_queue", message, priority)

            # Update metrics
            self.submitted_counter.inc()

            self.logger.info(f"Submitted transaction: {transaction.transaction_id}")

            return transaction.transaction_id

        except Exception as e:
            self.logger.error(f"Transaction submission failed: {str(e)}")
            raise

    def _calculate_checksum(self, transaction: Transaction) -> str:
        """Calculate transaction checksum"""
        data = f"{transaction.transaction_id}{transaction.user_id}{transaction.amount}{transaction.currency}{transaction.source_account}{transaction.destination_account}"
        return hashlib.sha256(data.encode()).hexdigest()

    def _store_transaction(self, transaction: Transaction):
        """Store transaction in database"""
        try:
            tx_log = TransactionLog(
                transaction_id=transaction.transaction_id,
                user_id=transaction.user_id,
                transaction_type=transaction.transaction_type,
                amount=transaction.amount,
                currency=transaction.currency,
                source_account=transaction.source_account,
                destination_account=transaction.destination_account,
                status=transaction.status.value,
                priority=transaction.priority.value,
                metadata=json.dumps(transaction.metadata),
                checksum=transaction.checksum,
            )

            self.db_session.add(tx_log)
            self.db_session.commit()

        except Exception as e:
            self.logger.error(f"Transaction storage failed: {str(e)}")
            self.db_session.rollback()
            raise

    def get_transaction_status(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """Get transaction status"""
        try:
            # Check Redis cache first
            status_key = f"transaction_status:{transaction_id}"
            cached_status = self.redis_client.get(status_key)

            if cached_status:
                return json.loads(cached_status)

            # Check database
            tx_log = (
                self.db_session.query(TransactionLog)
                .filter_by(transaction_id=transaction_id)
                .first()
            )

            if tx_log:
                return {
                    "transaction_id": tx_log.transaction_id,
                    "status": tx_log.status,
                    "processing_node": tx_log.processing_node,
                    "created_at": tx_log.created_at.isoformat(),
                    "updated_at": tx_log.updated_at.isoformat(),
                    "completed_at": (
                        tx_log.completed_at.isoformat() if tx_log.completed_at else None
                    ),
                    "processing_time": tx_log.processing_time,
                    "error_message": tx_log.error_message,
                }

            return None

        except Exception as e:
            self.logger.error(f"Status retrieval failed: {str(e)}")
            return None

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics"""
        try:
            # Queue sizes
            queue_sizes = {}
            for priority in Priority:
                size = self.message_queue.get_queue_size(
                    f"transaction_queue_{priority.name.lower()}"
                )
                queue_sizes[priority.name.lower()] = size
                self.queue_size_gauge.labels(priority=priority.name.lower()).set(size)

            # Processing statistics
            recent_transactions = (
                self.db_session.query(TransactionLog)
                .filter(
                    TransactionLog.created_at
                    >= datetime.utcnow() - timedelta(minutes=5)
                )
                .all()
            )

            total_recent = len(recent_transactions)
            completed_recent = len(
                [tx for tx in recent_transactions if tx.status == "completed"]
            )
            failed_recent = len(
                [tx for tx in recent_transactions if tx.status == "failed"]
            )

            # Calculate throughput (transactions per second)
            throughput = total_recent / 300.0  # 5 minutes = 300 seconds
            self.throughput_gauge.set(throughput)

            # Average processing time
            processing_times = [
                tx.processing_time for tx in recent_transactions if tx.processing_time
            ]
            avg_processing_time = (
                sum(processing_times) / len(processing_times) if processing_times else 0
            )

            # Node health
            healthy_nodes = len(self.load_balancer._get_healthy_nodes())
            total_nodes = len(self.load_balancer.nodes)

            return {
                "queue_sizes": queue_sizes,
                "total_recent_transactions": total_recent,
                "completed_recent": completed_recent,
                "failed_recent": failed_recent,
                "success_rate": (
                    completed_recent / total_recent if total_recent > 0 else 0
                ),
                "throughput_tps": throughput,
                "avg_processing_time": avg_processing_time,
                "healthy_nodes": healthy_nodes,
                "total_nodes": total_nodes,
                "node_health_ratio": (
                    healthy_nodes / total_nodes if total_nodes > 0 else 0
                ),
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Metrics calculation failed: {str(e)}")
            return {"error": str(e)}

    def stop_processing(self):
        """Stop transaction processing"""
        self.is_running = False
        self.logger.info("Stopping transaction processing")


def create_distributed_transaction_manager(
    config: Dict[str, Any],
) -> DistributedTransactionManager:
    """Factory function to create distributed transaction manager"""
    return DistributedTransactionManager(config)


if __name__ == "__main__":
    # Example usage
    import structlog

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configuration
    config = {
        "queue_type": "redis",
        "queue_config": {"redis_url": "redis://localhost:6379/0"},
        "database_url": "postgresql://localhost/nexafi",
        "redis_url": "redis://localhost:6379/0",
    }

    # Create transaction manager
    manager = create_distributed_transaction_manager(config)

    # Example transaction
    transaction = Transaction(
        transaction_id="",
        user_id="user123",
        transaction_type="transfer",
        amount=1000.0,
        currency="USD",
        source_account="acc_source_123",
        destination_account="acc_dest_456",
        metadata={"description": "Test transfer"},
        priority=Priority.NORMAL,
        timestamp=datetime.utcnow(),
        status=TransactionStatus.PENDING,
    )

    # Submit transaction
    tx_id = manager.submit_transaction(transaction)
    logger.info(f"Submitted transaction: {tx_id}")
    # Start processing (in production, this would run in separate processes)
    # manager.start_processing(num_workers=4)

    # Get system metrics
    metrics = manager.get_system_metrics()
    logger.info(f"System Metrics: {json.dumps(metrics, indent=2)}")
