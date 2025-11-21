import pytest

from bdr.models import DecisionReceipt, DecisionType
from bdr.receipts import DecisionReceiptEmitter, ReceiptEmissionError


def test_receipt_emitter_handles_sink_errors():
    def sink(_receipt):
        raise RuntimeError("sink failure")

    emitter = DecisionReceiptEmitter(sink=sink)
    receipt = DecisionReceipt(
        decision_type=DecisionType.BACKUP_RUN_COMPLETED,
        operation_id="op1",
    )
    with pytest.raises(ReceiptEmissionError):
        emitter.emit(receipt)

