"""
Action composition utilities for MMM Engine.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any, Dict, List

from .models import MMMAction, ActionType, Surface, MMMContext
from .service_registry import get_llm_gateway

logger = logging.getLogger(__name__)


class ActionComposer:
    """Converts playbook action definitions into MMMAction objects."""

    def __init__(self) -> None:
        self.llm_gateway = get_llm_gateway()

    def compose_actions(self, playbook_name: str, action_defs: List[Dict[str, Any]], context: MMMContext) -> List[MMMAction]:
        actions: List[MMMAction] = []
        for definition in action_defs:
            try:
                actions.append(self._compose_action(playbook_name, definition, context))
            except Exception as exc:  # pragma: no cover - defensive
                logger.exception("Failed to compose action: %s", exc)
        return actions

    def _compose_action(self, playbook_name: str, definition: Dict[str, Any], context: MMMContext) -> MMMAction:
        action_type = ActionType(definition.get("type", "mirror"))
        payload = definition.get("payload", {})

        if action_type in {ActionType.MENTOR, ActionType.MULTIPLIER} and definition.get("llm_prompt"):
            prompt = definition["llm_prompt"].format(actor=context.actor_id or "engineer")
            payload = asyncio.run(self._generate_llm_content(prompt, payload))

        surfaces = [Surface(surface) for surface in definition.get("surfaces", ["ide"])]
        requires_consent = definition.get("requires_consent", action_type == ActionType.MULTIPLIER)
        requires_dual = definition.get("requires_dual_channel", False)

        return MMMAction(
            action_id=str(uuid.uuid4()),
            type=action_type,
            surfaces=surfaces,
            payload={
                "title": payload.get("title") or f"{playbook_name} {action_type.value.title()}",
                "body": payload.get("body") or "Action payload pending template implementation.",
            },
            requires_consent=requires_consent,
            requires_dual_channel=requires_dual,
        )

    async def _generate_llm_content(self, prompt: str, fallback_payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            response = await self.llm_gateway.generate(prompt, {})
            return {
                "title": fallback_payload.get("title") or "Mentor suggestion",
                "body": response["content"],
                "safety": response["safety"],
            }
        except Exception as exc:
            logger.warning("LLM generation failed, falling back. Error=%s", exc)
            return fallback_payload or {"title": "Mentor suggestion", "body": "Fallback guidance."}


