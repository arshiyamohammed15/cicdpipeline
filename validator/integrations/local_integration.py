"""
Local deterministic integration for offline demos and tests.
"""

from typing import Dict, Any

from .ai_service_wrapper import AIServiceIntegration


class LocalIntegration(AIServiceIntegration):
    """Local integration that returns deterministic output without network calls."""

    def __init__(self) -> None:
        super().__init__("local")

    def generate_code(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate code through the local stub with validation."""
        return self._validate_and_generate(prompt, context)

    def _call_ai_service(self, prompt: str, context: Dict[str, Any]) -> str:
        """Return deterministic code for offline validation demos."""
        file_type = (context.get("file_type") or "python").lower()

        if file_type in {"typescript", "ts", "javascript", "js"}:
            return "export function add(a: number, b: number): number {\n  return a + b;\n}\n"

        if file_type in {"python", "py"}:
            return "def add(a, b):\n    return a + b\n"

        return "add(a, b) = a + b\n"
