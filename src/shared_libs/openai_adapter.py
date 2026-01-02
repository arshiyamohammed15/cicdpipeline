"""
OpenAI v1 adapter with deterministic offline behavior.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional


def _use_real_services() -> bool:
    return os.getenv("USE_REAL_SERVICES", "").lower() == "true"


def _require_api_key() -> str:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY must be set when USE_REAL_SERVICES=true")
    return api_key


def _resolve_model(model: Optional[str]) -> str:
    model_name = (model or os.getenv("OPENAI_MODEL", "")).strip()
    if not model_name:
        raise RuntimeError("OPENAI_MODEL must be set when USE_REAL_SERVICES=true")
    return model_name


def llm_generate_text(
    prompt: str,
    system_message: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Generate text using OpenAI v1 Responses API or return a deterministic stub.
    """
    if not _use_real_services():
        return {
            "output_text": prompt,
            "used_stub": True,
            "model": (model or os.getenv("OPENAI_MODEL")),
        }

    api_key = _require_api_key()
    model_name = _resolve_model(model)

    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    messages = [{"role": "user", "content": prompt}]
    if system_message:
        messages.insert(0, {"role": "system", "content": system_message})

    create_kwargs: Dict[str, Any] = {
        "model": model_name,
        "input": messages,
    }
    if temperature is not None:
        create_kwargs["temperature"] = temperature
    if max_tokens is not None:
        create_kwargs["max_output_tokens"] = max_tokens

    response = client.responses.create(**create_kwargs)
    return {
        "output_text": response.output_text,
        "used_stub": False,
        "model": model_name,
    }


def llm_edit_text(
    original_text: str,
    instruction: str,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Apply edits using Responses API; stub returns the original text unchanged.
    """
    prompt = (
        "Apply the requested edits to the input text.\n\n"
        f"Edits:\n{instruction}\n\n"
        f"Input:\n{original_text}\n\n"
        "Return only the updated text."
    )
    return llm_generate_text(
        prompt=prompt,
        system_message=None,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
