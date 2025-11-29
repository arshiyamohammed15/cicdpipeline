"""
PM-3 (Signal Ingestion) client for Integration Adapters Module.

What: Client for forwarding SignalEnvelope events to PM-3 per FR-6
Why: Integrate with PM-3 for signal ingestion
Reads/Writes: PM-3 ingestion API
Contracts: PRD FR-6 (Event Normalisation)
Risks: PM-3 API changes, network failures
"""

from __future__ import annotations

import os
from typing import List, Optional

import httpx

# Import SignalEnvelope - try multiple paths
try:
    from signal_ingestion_normalization.models import SignalEnvelope
except ImportError:
    try:
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../product_services/signal-ingestion-normalization"))
        from models import SignalEnvelope
    except ImportError:
        # Fallback: define minimal SignalEnvelope
        from typing import Any, Dict
        from datetime import datetime
        from pydantic import BaseModel, Field
        from enum import Enum
        
        class SignalKind(str, Enum):
            EVENT = "event"
        
        class Environment(str, Enum):
            PROD = "prod"
        
        class SignalEnvelope(BaseModel):
            signal_id: str
            tenant_id: str
            environment: Environment
            producer_id: str
            signal_kind: SignalKind
            signal_type: str
            occurred_at: datetime
            ingested_at: datetime
            payload: Dict[str, Any]
            schema_version: str


class PM3Client:
    """Client for PM-3 Signal Ingestion service."""

    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize PM-3 client.
        
        Args:
            base_url: PM-3 service base URL (defaults to environment variable)
        """
        self.base_url = base_url or os.getenv(
            "PM3_SERVICE_URL",
            "http://localhost:8000"
        ).rstrip("/")
        self.client = httpx.Client(timeout=30.0)

    def ingest_signal(self, signal: SignalEnvelope) -> bool:
        """
        Ingest a single SignalEnvelope to PM-3.
        
        Args:
            signal: SignalEnvelope to ingest
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = self.client.post(
                f"{self.base_url}/v1/signals/ingest",
                json=signal.model_dump(),
            )
            response.raise_for_status()
            return True
        except Exception:
            return False

    def ingest_signals(self, signals: List[SignalEnvelope]) -> int:
        """
        Ingest multiple SignalEnvelope events to PM-3 (batch).
        
        Args:
            signals: List of SignalEnvelope to ingest
            
        Returns:
            Number of successfully ingested signals
        """
        if not signals:
            return 0
        
        try:
            response = self.client.post(
                f"{self.base_url}/v1/signals/ingest/batch",
                json={"signals": [s.model_dump() for s in signals]},
            )
            response.raise_for_status()
            return len(signals)
        except Exception:
            return 0

    def close(self) -> None:
        """Close HTTP client."""
        self.client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

