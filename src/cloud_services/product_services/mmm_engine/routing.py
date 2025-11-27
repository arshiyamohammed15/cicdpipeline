"""
Surface routing utilities for MMM actions.
"""

from __future__ import annotations

from typing import List

from .models import MMMAction, Surface


class SurfaceRouter:
    """Applies per-surface payload adaptations."""

    def route(self, actions: List[MMMAction]) -> List[MMMAction]:
        routed = []
        for action in actions:
            payload = dict(action.payload)
            if Surface.IDE in action.surfaces:
                payload.setdefault("presentation", {}).update({"variant": "card"})
            if Surface.CI in action.surfaces:
                payload.setdefault("presentation", {}).update({"variant": "check-summary"})
            if Surface.ALERT in action.surfaces:
                payload.setdefault("presentation", {}).update({"variant": "notification"})
            routed.append(
                MMMAction(
                    action_id=action.action_id,
                    type=action.type,
                    surfaces=action.surfaces,
                    payload=payload,
                    requires_consent=action.requires_consent,
                    requires_dual_channel=action.requires_dual_channel,
                )
            )
        return routed


