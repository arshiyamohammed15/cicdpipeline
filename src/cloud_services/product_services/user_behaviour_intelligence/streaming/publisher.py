"""
Event Stream Publisher for UBI Module (EPC-9).

What: Publishes BehaviouralSignals to event stream
Why: Enable MMM and Detection Engine consumption per PRD FR-11
Reads/Writes: Event stream publishing
Contracts: UBI PRD FR-11, Section 11.3
Risks: Stream failures, backpressure issues
"""

import logging
import json
from typing import Dict, Any, Optional, Callable
from collections import deque

from ..models import BehaviouralSignal, Severity
from .event_bus import EventBus, create_event_bus

logger = logging.getLogger(__name__)


class EventStreamPublisher:
    """
    Event stream publisher for BehaviouralSignals.

    Per UBI PRD FR-11:
    - Publish to ubi.behavioural_signals stream
    - At-least-once delivery semantics
    - DLQ routing for failed deliveries
    - Backpressure handling
    - Stream filtering: MMM (all signals), Detection Engine (high-severity only)
    """

    STREAM_NAME = "ubi.behavioural_signals"

    def __init__(
        self,
        buffer_size: int = 1000,
        rate_limit_per_second: int = 100,
        event_bus: Optional[EventBus] = None
    ):
        """
        Initialize event stream publisher.

        Args:
            buffer_size: Buffer size for backpressure handling
            rate_limit_per_second: Rate limit per second
            event_bus: Optional event bus instance (default: auto-create)
        """
        self.buffer_size = buffer_size
        self.rate_limit_per_second = rate_limit_per_second
        
        # Event bus
        self.event_bus = event_bus or create_event_bus()
        
        # Signal buffer
        self.signal_buffer: deque = deque()
        
        # Consumer handlers (for backward compatibility)
        self.mmm_handler: Optional[Callable] = None
        self.detection_handler: Optional[Callable] = None
        
        # DLQ for failed deliveries
        self.dlq: deque = deque()
        
        # Metrics
        self.signals_published = 0
        self.signals_failed = 0
        self.backpressure_count = 0

    def register_mmm_consumer(self, handler: Callable[[Dict[str, Any]], bool]) -> None:
        """
        Register MMM consumer handler.

        Args:
            handler: Handler function that takes signal dict and returns success bool
        """
        self.mmm_handler = handler
        logger.info("MMM consumer registered")

    def register_detection_consumer(self, handler: Callable[[Dict[str, Any]], bool]) -> None:
        """
        Register Detection Engine consumer handler.

        Args:
            handler: Handler function that takes signal dict and returns success bool
        """
        self.detection_handler = handler
        logger.info("Detection Engine consumer registered")

    async def publish_signal(self, signal: BehaviouralSignal) -> bool:
        """
        Publish signal to event stream.

        Args:
            signal: BehaviouralSignal to publish

        Returns:
            True if published successfully, False otherwise
        """
        try:
            # Check backpressure
            if len(self.signal_buffer) >= self.buffer_size:
                self.backpressure_count += 1
                logger.warning("Signal buffer full, dropping signal")
                return False
            
            # Serialize signal
            signal_dict = signal.model_dump()
            
            # Publish to event bus (all signals go to MMM)
            success = await self.event_bus.publish(
                topic="ubi.behavioural_signals",
                message=signal_dict,
                key=signal.tenant_id  # Partition by tenant
            )
            
            if not success:
                logger.warning("Failed to publish signal to event bus")
                self.dlq.append(signal_dict)
                self.signals_failed += 1
                return False
            
            # Publish to Detection Engine topic (high-severity only)
            if signal.severity in [Severity.WARN, Severity.CRITICAL]:
                detection_success = await self.event_bus.publish(
                    topic="ubi.behavioural_signals.detection",
                    message=signal_dict,
                    key=signal.tenant_id
                )
                
                if not detection_success:
                    logger.warning("Failed to publish high-severity signal to detection topic")
                    # Don't fail overall - MMM got the signal
            
            # Backward compatibility: call handlers if registered
            if self.mmm_handler:
                try:
                    handler_success = self.mmm_handler(signal_dict)
                    if not handler_success:
                        logger.warning("MMM handler returned failure")
                except Exception as e:
                    logger.error(f"MMM handler error: {e}")
            
            if self.detection_handler and signal.severity in [Severity.WARN, Severity.CRITICAL]:
                try:
                    handler_success = self.detection_handler(signal_dict)
                    if not handler_success:
                        logger.warning("Detection handler returned failure")
                except Exception as e:
                    logger.error(f"Detection handler error: {e}")
            
            self.signals_published += 1
            return True
        except Exception as e:
            logger.error(f"Error publishing signal: {e}", exc_info=True)
            self.signals_failed += 1
            return False

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get publisher metrics.

        Returns:
            Metrics dictionary
        """
        return {
            "signals_published": self.signals_published,
            "signals_failed": self.signals_failed,
            "backpressure_count": self.backpressure_count,
            "buffer_size": len(self.signal_buffer),
            "dlq_size": len(self.dlq)
        }

