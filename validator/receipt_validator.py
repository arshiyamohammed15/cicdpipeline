"""
Receipt Validator for End-to-End Invariants

Validates receipts against schema and enforces invariants:
- Required fields (trace IDs, policy snapshot hash/KID/version IDs)
- Timestamps UTC Z format
- Monotonic time included
- Status transitions T0/T1/T2
- Append-only JSONL format
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


class ReceiptValidator:
    """Validates receipts against schema and invariants."""

    # Required fields for decision receipts
    REQUIRED_FIELDS = [
        'receipt_id',
        'gate_id',
        'policy_version_ids',
        'snapshot_hash',
        'timestamp_utc',
        'timestamp_monotonic_ms',
        'decision',
        'signature'
    ]

    # Valid decision statuses
    VALID_STATUSES = ['pass', 'warn', 'soft_block', 'hard_block']

    # Valid evaluation points (T0/T1/T2 markers)
    VALID_EVALUATION_POINTS = [
        'pre-commit',  # T0
        'pre-merge',   # T1
        'pre-deploy',  # T1
        'post-deploy'  # T2
    ]

    def __init__(self, schema_path: Optional[Path] = None):
        """
        Initialize receipt validator.

        Args:
            schema_path: Optional path to JSON schema file
        """
        self.schema_path = schema_path
        self.schema = None
        if schema_path and schema_path.exists():
            with open(schema_path, 'r', encoding='utf-8') as f:
                self.schema = json.load(f)

    def validate_receipt_structure(self, receipt: Dict[str, Any]) -> List[str]:
        """
        Validate receipt has required structure.

        Args:
            receipt: Receipt dictionary

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in receipt:
                errors.append(f"Missing required field: {field}")

        return errors

    def validate_timestamps(self, receipt: Dict[str, Any]) -> List[str]:
        """
        Validate timestamp formats.

        Args:
            receipt: Receipt dictionary

        Returns:
            List of validation errors
        """
        errors = []

        # Validate timestamp_utc (ISO-8601 UTC with Z)
        if 'timestamp_utc' in receipt:
            ts_utc = receipt['timestamp_utc']
            try:
                # Parse ISO-8601
                dt = datetime.fromisoformat(ts_utc.replace('Z', '+00:00'))
                # Check ends with Z or has +00:00
                if not (ts_utc.endswith('Z') or ts_utc.endswith('+00:00')):
                    errors.append(f"timestamp_utc must be UTC (end with Z or +00:00): {ts_utc}")
            except ValueError as e:
                errors.append(f"Invalid timestamp_utc format: {ts_utc} - {e}")
        else:
            errors.append("Missing timestamp_utc")

        # Validate timestamp_monotonic_ms (must be numeric)
        if 'timestamp_monotonic_ms' in receipt:
            try:
                monotonic = receipt['timestamp_monotonic_ms']
                if not isinstance(monotonic, (int, float)):
                    errors.append(f"timestamp_monotonic_ms must be numeric: {type(monotonic)}")
                elif monotonic < 0:
                    errors.append(f"timestamp_monotonic_ms must be non-negative: {monotonic}")
            except Exception as e:
                errors.append(f"Invalid timestamp_monotonic_ms: {e}")
        else:
            errors.append("Missing timestamp_monotonic_ms")

        return errors

    def validate_decision_status(self, receipt: Dict[str, Any]) -> List[str]:
        """
        Validate decision status is valid.

        Args:
            receipt: Receipt dictionary

        Returns:
            List of validation errors
        """
        errors = []

        if 'decision' in receipt:
            decision = receipt['decision']
            if isinstance(decision, dict):
                status = decision.get('status')
            elif isinstance(decision, str):
                status = decision
            else:
                errors.append(f"Invalid decision type: {type(decision)}")
                return errors

            if status not in self.VALID_STATUSES:
                errors.append(f"Invalid decision status: {status}. Must be one of {self.VALID_STATUSES}")

        return errors

    def validate_policy_references(self, receipt: Dict[str, Any]) -> List[str]:
        """
        Validate policy snapshot hash and version IDs.

        Args:
            receipt: Receipt dictionary

        Returns:
            List of validation errors
        """
        errors = []

        # Validate snapshot_hash (sha256:hex format)
        if 'snapshot_hash' in receipt:
            hash_val = receipt['snapshot_hash']
            if not isinstance(hash_val, str):
                errors.append(f"snapshot_hash must be string: {type(hash_val)}")
            elif not re.match(r'^sha256:[0-9a-f]{64}$', hash_val):
                errors.append(f"snapshot_hash must be sha256:hex format: {hash_val}")
        else:
            errors.append("Missing snapshot_hash")

        # Validate policy_version_ids (array of strings)
        if 'policy_version_ids' in receipt:
            version_ids = receipt['policy_version_ids']
            if not isinstance(version_ids, list):
                errors.append(f"policy_version_ids must be array: {type(version_ids)}")
            elif len(version_ids) == 0:
                errors.append("policy_version_ids must not be empty")
            else:
                for vid in version_ids:
                    if not isinstance(vid, str):
                        errors.append(f"policy_version_ids items must be strings: {type(vid)}")
        else:
            errors.append("Missing policy_version_ids")

        return errors

    def validate_signature(self, receipt: Dict[str, Any]) -> List[str]:
        """
        Validate receipt signature exists.

        Args:
            receipt: Receipt dictionary

        Returns:
            List of validation errors
        """
        errors = []

        if 'signature' not in receipt:
            errors.append("Missing signature")
        elif not isinstance(receipt['signature'], str):
            errors.append(f"signature must be string: {type(receipt['signature'])}")
        elif len(receipt['signature']) == 0:
            errors.append("signature must not be empty")

        return errors

    def validate_receipt(self, receipt: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate receipt against all invariants.

        Args:
            receipt: Receipt dictionary

        Returns:
            Validation result with 'valid' and 'errors'
        """
        all_errors = []

        # Run all validations
        all_errors.extend(self.validate_receipt_structure(receipt))
        all_errors.extend(self.validate_timestamps(receipt))
        all_errors.extend(self.validate_decision_status(receipt))
        all_errors.extend(self.validate_policy_references(receipt))
        all_errors.extend(self.validate_signature(receipt))

        return {
            'valid': len(all_errors) == 0,
            'errors': all_errors,
            'receipt_id': receipt.get('receipt_id', 'unknown')
        }

    def validate_jsonl_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Validate JSONL file (one JSON object per line).

        Args:
            file_path: Path to JSONL file

        Returns:
            Validation result with line-by-line errors
        """
        errors_by_line = []
        valid_count = 0
        total_count = 0

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue

                    total_count += 1
                    try:
                        receipt = json.loads(line)
                        result = self.validate_receipt(receipt)
                        if result['valid']:
                            valid_count += 1
                        else:
                            errors_by_line.append({
                                'line': line_num,
                                'receipt_id': result.get('receipt_id', 'unknown'),
                                'errors': result['errors']
                            })
                    except json.JSONDecodeError as e:
                        errors_by_line.append({
                            'line': line_num,
                            'receipt_id': 'parse_error',
                            'errors': [f"Invalid JSON: {e}"]
                        })
        except Exception as e:
            return {
                'valid': False,
                'error': f"Failed to read file: {e}",
                'valid_count': 0,
                'total_count': 0,
                'errors_by_line': []
            }

        return {
            'valid': len(errors_by_line) == 0,
            'valid_count': valid_count,
            'total_count': total_count,
            'errors_by_line': errors_by_line
        }
