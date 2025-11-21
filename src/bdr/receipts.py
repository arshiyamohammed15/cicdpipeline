"""Decision receipt integration for BDR."""

from __future__ import annotations

from typing import Callable, List, Optional

from .models import DecisionReceipt


class ReceiptEmissionError(RuntimeError):
    """Raised when receipt emission fails."""


class DecisionReceiptEmitter:
    """Collects and forwards Decision Receipts to the shared infrastructure."""

    def __init__(self, sink: Optional[Callable[[DecisionReceipt], None]] = None) -> None:
        self._sink = sink
        self._captured: List[DecisionReceipt] = []

    def emit(self, receipt: DecisionReceipt) -> None:
        self._captured.append(receipt)
        if self._sink:
            try:
                self._sink(receipt)
            except Exception as exc:  # noqa: BLE001
                msg = f"Failed to emit receipt {receipt.decision_type}"
                raise ReceiptEmissionError(msg) from exc

    @property
    def captured(self) -> List[DecisionReceipt]:
        return list(self._captured)

