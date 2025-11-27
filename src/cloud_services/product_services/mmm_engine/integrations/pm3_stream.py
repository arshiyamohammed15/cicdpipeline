"""
PM-3 Signal stream integration for MMM Engine.

Supports Kafka, RabbitMQ, and in-memory modes so MMM can ingest canonical
SignalEnvelope events directly from PM-3 (SIN) routing.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
from typing import Any, Awaitable, Callable, Optional

from .signal_bus import SignalEnvelope

logger = logging.getLogger(__name__)


class PM3EventStream:
    """Background consumer that forwards PM-3 signals into MMMService."""

    def __init__(
        self,
        handler: Callable[[SignalEnvelope], Awaitable[None]],
        *,
        bus_type: Optional[str] = None,
    ) -> None:
        self.handler = handler
        self.bus_type = (bus_type or os.getenv("MMM_EVENT_BUS_TYPE", "in_memory")).lower()
        self.topic = os.getenv("PM3_EVENT_TOPIC", "pm3.signals.normalized")
        self.group_id = os.getenv("PM3_EVENT_GROUP_ID", "mmm-engine")
        self._task: Optional[asyncio.Task] = None
        self._consumer = None
        self._connection = None

    async def start(self) -> None:
        if self.bus_type == "kafka":
            await self._start_kafka()
        elif self.bus_type == "rabbitmq":
            await self._start_rabbitmq()
        else:
            logger.info("PM3 event stream running in in-memory mode")

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None
        if self.bus_type == "kafka" and self._consumer:
            await self._consumer.stop()
            self._consumer = None
        if self.bus_type == "rabbitmq" and self._connection:
            await self._connection.close()
            self._connection = None

    async def _start_kafka(self) -> None:
        try:
            from aiokafka import AIOKafkaConsumer
        except ImportError as exc:  # pragma: no cover - requires optional dependency
            raise RuntimeError("aiokafka must be installed for Kafka integration") from exc

        bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self._consumer = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=bootstrap_servers.split(","),
            group_id=self.group_id,
            enable_auto_commit=True,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        )
        await self._consumer.start()
        logger.info("PM3 Kafka consumer started for topic %s", self.topic)
        self._task = asyncio.create_task(self._consume_kafka())

    async def _consume_kafka(self) -> None:
        assert self._consumer is not None
        try:
            async for msg in self._consumer:
                await self._dispatch(msg.value)
        except Exception as exc:  # pragma: no cover
            logger.exception("Kafka consumer error: %s", exc)

    async def _start_rabbitmq(self) -> None:
        try:
            import aio_pika
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("aio-pika must be installed for RabbitMQ integration") from exc

        connection_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
        exchange_name = os.getenv("PM3_EVENT_EXCHANGE", "pm3.signals")
        queue_name = os.getenv("PM3_EVENT_QUEUE", f"{self.group_id}.{self.topic}")

        self._connection = await aio_pika.connect_robust(connection_url)
        channel = await self._connection.channel()
        exchange = await channel.declare_exchange(exchange_name, aio_pika.ExchangeType.TOPIC, durable=True)
        queue = await channel.declare_queue(queue_name, durable=True)
        routing_key = os.getenv("PM3_EVENT_ROUTING_KEY", self.topic)
        await queue.bind(exchange, routing_key)

        async def _rabbit_consumer(message: aio_pika.IncomingMessage) -> None:
            async with message.process():
                payload = json.loads(message.body.decode("utf-8"))
                await self._dispatch(payload)

        await queue.consume(_rabbit_consumer)
        logger.info("PM3 RabbitMQ consumer bound to %s/%s", exchange_name, routing_key)

    async def _dispatch(self, payload: dict[str, Any]) -> None:
        try:
            envelope = SignalEnvelope.from_dict(payload)
            await self.handler(envelope)
        except Exception as exc:  # pragma: no cover
            logger.exception("Failed to process PM3 signal: %s", exc)



