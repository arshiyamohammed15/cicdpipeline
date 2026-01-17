"""
Python instrumentation for ZeroUI Observability Layer.

Async/non-blocking telemetry emission for Cloud Services (Tier 3).
"""

from .instrumentation import EventEmitter, get_event_emitter

__all__ = ["EventEmitter", "get_event_emitter"]
