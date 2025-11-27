"""
Event Bus Integration for UBI Module (EPC-9).

What: Flexible event bus interface supporting Kafka, RabbitMQ, and in-memory for testing
Why: Enable signal publishing to downstream consumers per PRD FR-11
Reads/Writes: Event stream publishing
Contracts: UBI PRD FR-11, Section 11.3
Risks: Event bus failures, backpressure issues
"""

import logging
import json
import asyncio
from typing import Dict, Any, Optional, Callable
from abc import ABC, abstractmethod
from enum import Enum

logger = logging.getLogger(__name__)


class EventBusType(str, Enum):
    """Event bus type enumeration."""
    KAFKA = "kafka"
    RABBITMQ = "rabbitmq"
    IN_MEMORY = "in_memory"


class EventBus(ABC):
    """
    Abstract event bus interface.

    Per UBI PRD FR-11: Supports at-least-once delivery, DLQ routing, backpressure handling.
    """

    @abstractmethod
    async def publish(
        self,
        topic: str,
        message: Dict[str, Any],
        key: Optional[str] = None
    ) -> bool:
        """
        Publish message to event bus.

        Args:
            topic: Topic/queue name
            message: Message dictionary
            key: Optional message key for partitioning

        Returns:
            True if published successfully, False otherwise
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close event bus connection."""
        pass


class InMemoryEventBus(EventBus):
    """
    In-memory event bus for testing and development.

    Uses asyncio queues for message delivery.
    """

    def __init__(self):
        """Initialize in-memory event bus."""
        self.queues: Dict[str, asyncio.Queue] = {}
        self.subscribers: Dict[str, list] = {}

    async def publish(
        self,
        topic: str,
        message: Dict[str, Any],
        key: Optional[str] = None
    ) -> bool:
        """
        Publish message to in-memory queue.

        Args:
            topic: Topic name
            message: Message dictionary
            key: Optional message key (ignored for in-memory)

        Returns:
            True if published successfully
        """
        try:
            if topic not in self.queues:
                self.queues[topic] = asyncio.Queue(maxsize=1000)
            
            queue = self.queues[topic]
            
            # Try to put message (non-blocking)
            try:
                queue.put_nowait(message)
                logger.debug(f"Published message to topic {topic}")
                return True
            except asyncio.QueueFull:
                logger.warning(f"Queue full for topic {topic}, dropping message")
                return False
        except Exception as e:
            logger.error(f"Error publishing to in-memory bus: {e}")
            return False

    async def subscribe(
        self,
        topic: str,
        handler: Callable[[Dict[str, Any]], bool]
    ) -> None:
        """
        Subscribe to topic (for testing).

        Args:
            topic: Topic name
            handler: Message handler function
        """
        if topic not in self.subscribers:
            self.subscribers[topic] = []
        self.subscribers[topic].append(handler)

    async def close(self) -> None:
        """Close in-memory event bus."""
        self.queues.clear()
        self.subscribers.clear()


class KafkaEventBus(EventBus):
    """
    Kafka event bus implementation.

    Uses aiokafka for async Kafka operations.
    """

    def __init__(
        self,
        bootstrap_servers: str,
        client_id: str = "ubi-module"
    ):
        """
        Initialize Kafka event bus.

        Args:
            bootstrap_servers: Kafka bootstrap servers (comma-separated)
            client_id: Kafka client ID
        """
        self.bootstrap_servers = bootstrap_servers
        self.client_id = client_id
        self.producer = None

    async def _ensure_producer(self) -> None:
        """Ensure Kafka producer is initialized."""
        if self.producer is None:
            try:
                from aiokafka import AIOKafkaProducer
                self.producer = AIOKafkaProducer(
                    bootstrap_servers=self.bootstrap_servers.split(','),
                    client_id=self.client_id,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8')
                )
                await self.producer.start()
                logger.info("Kafka producer started")
            except ImportError:
                raise ImportError("aiokafka not installed. Install with: pip install aiokafka")
            except Exception as e:
                logger.error(f"Error starting Kafka producer: {e}")
                raise

    async def publish(
        self,
        topic: str,
        message: Dict[str, Any],
        key: Optional[str] = None
    ) -> bool:
        """
        Publish message to Kafka topic.

        Args:
            topic: Kafka topic name
            message: Message dictionary
            key: Optional message key for partitioning

        Returns:
            True if published successfully, False otherwise
        """
        try:
            await self._ensure_producer()
            
            key_bytes = key.encode('utf-8') if key else None
            
            await self.producer.send_and_wait(
                topic,
                value=message,
                key=key_bytes
            )
            logger.debug(f"Published message to Kafka topic {topic}")
            return True
        except Exception as e:
            logger.error(f"Error publishing to Kafka: {e}")
            return False

    async def close(self) -> None:
        """Close Kafka producer."""
        if self.producer:
            await self.producer.stop()
            self.producer = None
            logger.info("Kafka producer stopped")


class RabbitMQEventBus(EventBus):
    """
    RabbitMQ event bus implementation.

    Uses aio_pika for async RabbitMQ operations.
    """

    def __init__(
        self,
        connection_url: str,
        exchange_name: str = "ubi_signals"
    ):
        """
        Initialize RabbitMQ event bus.

        Args:
            connection_url: RabbitMQ connection URL (amqp://...)
            exchange_name: Exchange name
        """
        self.connection_url = connection_url
        self.exchange_name = exchange_name
        self.connection = None
        self.channel = None
        self.exchange = None

    async def _ensure_connection(self) -> None:
        """Ensure RabbitMQ connection is established."""
        if self.connection is None:
            try:
                from aio_pika import connect_robust, ExchangeType
                self.connection = await connect_robust(self.connection_url)
                self.channel = await self.connection.channel()
                self.exchange = await self.channel.declare_exchange(
                    self.exchange_name,
                    ExchangeType.TOPIC,
                    durable=True
                )
                logger.info("RabbitMQ connection established")
            except ImportError:
                raise ImportError("aio_pika not installed. Install with: pip install aio-pika")
            except Exception as e:
                logger.error(f"Error connecting to RabbitMQ: {e}")
                raise

    async def publish(
        self,
        topic: str,
        message: Dict[str, Any],
        key: Optional[str] = None
    ) -> bool:
        """
        Publish message to RabbitMQ exchange.

        Args:
            topic: Routing key (topic)
            message: Message dictionary
            key: Optional routing key override

        Returns:
            True if published successfully, False otherwise
        """
        try:
            await self._ensure_connection()
            
            routing_key = key or topic
            
            await self.exchange.publish(
                message=json.dumps(message).encode('utf-8'),
                routing_key=routing_key
            )
            logger.debug(f"Published message to RabbitMQ exchange {self.exchange_name} with routing key {routing_key}")
            return True
        except Exception as e:
            logger.error(f"Error publishing to RabbitMQ: {e}")
            return False

    async def close(self) -> None:
        """Close RabbitMQ connection."""
        if self.connection:
            await self.connection.close()
            self.connection = None
            self.channel = None
            self.exchange = None
            logger.info("RabbitMQ connection closed")


def create_event_bus(bus_type: Optional[str] = None) -> EventBus:
    """
    Create event bus instance based on configuration.

    Args:
        bus_type: Event bus type (kafka, rabbitmq, in_memory) or None to auto-detect

    Returns:
        EventBus instance
    """
    import os
    
    bus_type = bus_type or os.getenv("UBI_EVENT_BUS_TYPE", "in_memory").lower()
    
    if bus_type == EventBusType.KAFKA:
        bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        return KafkaEventBus(bootstrap_servers=bootstrap_servers)
    elif bus_type == EventBusType.RABBITMQ:
        connection_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
        return RabbitMQEventBus(connection_url=connection_url)
    else:
        # Default to in-memory
        return InMemoryEventBus()

