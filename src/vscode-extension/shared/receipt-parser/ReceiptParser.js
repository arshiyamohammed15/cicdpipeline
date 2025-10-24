"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ReceiptParser = void 0;
class ReceiptParser {
    parseDecisionReceipt(receiptJson) {
        try {
            const receipt = JSON.parse(receiptJson);
            return this.validateDecisionReceipt(receipt) ? receipt : null;
        }
        catch (error) {
            console.error('Failed to parse decision receipt:', error);
            return null;
        }
    }
    parseFeedbackReceipt(receiptJson) {
        try {
            const receipt = JSON.parse(receiptJson);
            return this.validateFeedbackReceipt(receipt) ? receipt : null;
        }
        catch (error) {
            console.error('Failed to parse feedback receipt:', error);
            return null;
        }
    }
    validateDecisionReceipt(receipt) {
        return (typeof receipt.receipt_id === 'string' &&
            typeof receipt.gate_id === 'string' &&
            Array.isArray(receipt.policy_version_ids) &&
            typeof receipt.snapshot_hash === 'string' &&
            typeof receipt.timestamp_utc === 'string' &&
            typeof receipt.timestamp_monotonic_ms === 'number' &&
            typeof receipt.inputs === 'object' &&
            typeof receipt.decision === 'object' &&
            typeof receipt.decision.status === 'string' &&
            typeof receipt.decision.rationale === 'string' &&
            Array.isArray(receipt.decision.badges) &&
            Array.isArray(receipt.evidence_handles) &&
            typeof receipt.actor === 'object' &&
            typeof receipt.actor.repo_id === 'string' &&
            typeof receipt.degraded === 'boolean' &&
            typeof receipt.signature === 'string');
    }
    validateFeedbackReceipt(receipt) {
        return (typeof receipt.feedback_id === 'string' &&
            typeof receipt.decision_receipt_id === 'string' &&
            typeof receipt.pattern_id === 'string' &&
            ['FB-01', 'FB-02', 'FB-03', 'FB-04'].includes(receipt.pattern_id) &&
            typeof receipt.choice === 'string' &&
            ['worked', 'partly', 'didnt'].includes(receipt.choice) &&
            Array.isArray(receipt.tags) &&
            typeof receipt.actor === 'object' &&
            typeof receipt.actor.repo_id === 'string' &&
            typeof receipt.timestamp_utc === 'string' &&
            typeof receipt.signature === 'string');
    }
    extractReceiptId(receipt) {
        return 'receipt_id' in receipt ? receipt.receipt_id : receipt.feedback_id;
    }
    isDecisionReceipt(receipt) {
        return 'gate_id' in receipt;
    }
    isFeedbackReceipt(receipt) {
        return 'pattern_id' in receipt;
    }
}
exports.ReceiptParser = ReceiptParser;
//# sourceMappingURL=ReceiptParser.js.map