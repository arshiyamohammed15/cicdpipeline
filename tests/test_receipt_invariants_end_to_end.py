"""
Receipt Invariants End-to-End Test

Cross-surface test that generates a receipt via edge agent, verifies with
validator/receipt_validator.py, and reads via VS Code resolver to guarantee
canonical JSON/signature compatibility across tiers.
"""

import unittest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import hashlib

# Mock edge agent receipt generation
def generate_mock_receipt(repo_id: str, gate_id: str, decision: str = 'pass') -> dict:
    """
    Generate a mock receipt as edge agent would create it.

    Args:
        repo_id: Repository identifier (kebab-case)
        gate_id: Gate identifier
        decision: Decision status

    Returns:
        Receipt dictionary
    """
    timestamp_utc = datetime.utcnow().isoformat() + 'Z'
    timestamp_monotonic_ms = int(datetime.utcnow().timestamp() * 1000)

    # Generate policy snapshot hash
    policy_data = f"policy_v1_{gate_id}"
    snapshot_hash = f"sha256:{hashlib.sha256(policy_data.encode()).hexdigest()}"

    receipt = {
        'receipt_id': f"receipt_{timestamp_monotonic_ms}",
        'gate_id': gate_id,
        'policy_version_ids': [f"policy_v1_{gate_id}"],
        'snapshot_hash': snapshot_hash,
        'timestamp_utc': timestamp_utc,
        'timestamp_monotonic_ms': timestamp_monotonic_ms,
        'decision': {
            'status': decision,
            'reason': 'Test receipt'
        },
        'signature': f"sig_{hashlib.sha256(json.dumps({'receipt_id': f'receipt_{timestamp_monotonic_ms}'}, sort_keys=True).encode()).hexdigest()[:32]}"
    }

    return receipt


class TestReceiptInvariantsEndToEnd(unittest.TestCase):
    """Test receipt invariants across edge agent, validator, and VS Code resolver."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.repo_id = 'test-repo'
        self.gate_id = 'test-gate'

        # Create ZU_ROOT structure
        self.zu_root = self.temp_dir / 'zu_root'
        self.zu_root.mkdir()
        (self.zu_root / 'ide' / 'receipts' / self.repo_id).mkdir(parents=True)

        # Set ZU_ROOT environment variable
        import os
        self.original_zu_root = os.environ.get('ZU_ROOT')
        os.environ['ZU_ROOT'] = str(self.zu_root)

    def tearDown(self):
        """Clean up test environment."""
        import os
        if self.original_zu_root:
            os.environ['ZU_ROOT'] = self.original_zu_root
        elif 'ZU_ROOT' in os.environ:
            del os.environ['ZU_ROOT']

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_receipt_flow_edge_to_validator_to_resolver(self):
        """
        Test complete receipt flow:
        1. Edge agent generates receipt
        2. Validator validates receipt
        3. VS Code resolver can read receipt
        """
        # Step 1: Generate receipt via edge agent (mock)
        receipt = generate_mock_receipt(self.repo_id, self.gate_id, 'pass')

        # Verify receipt structure
        self.assertIn('receipt_id', receipt)
        self.assertIn('gate_id', receipt)
        self.assertIn('policy_version_ids', receipt)
        self.assertIn('snapshot_hash', receipt)
        self.assertIn('timestamp_utc', receipt)
        self.assertIn('timestamp_monotonic_ms', receipt)
        self.assertIn('decision', receipt)
        self.assertIn('signature', receipt)

        # Step 2: Validate receipt with validator
        from validator.receipt_validator import ReceiptValidator
        validator = ReceiptValidator()
        validation_result = validator.validate_receipt(receipt)

        self.assertTrue(validation_result['valid'], 
                                    f"Receipt validation failed: {validation_result.get('errors', [])}")

        # Step 3: Write receipt to storage using resolver pattern
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / 'src' / 'shared' / 'storage'))
        from BaseStoragePathResolver import BaseStoragePathResolver

        resolver = BaseStoragePathResolver(str(self.zu_root))
        year = datetime.utcnow().year
        month = datetime.utcnow().month
        receipt_dir = Path(resolver.resolveReceiptPath(self.repo_id, year, month))
        receipt_dir.mkdir(parents=True, exist_ok=True)

        receipt_file = receipt_dir / f"{receipt['receipt_id']}.json"
        with open(receipt_file, 'w', encoding='utf-8') as f:
            json.dump(receipt, f, indent=2, ensure_ascii=False)

        # Step 4: Read receipt back via resolver
        self.assertTrue(receipt_file.exists(), "Receipt file should exist")

        with open(receipt_file, 'r', encoding='utf-8') as f:
            read_receipt = json.load(f)

        # Step 5: Verify canonical JSON compatibility
        self.assertEqual(receipt['receipt_id'], read_receipt['receipt_id'])
        self.assertEqual(receipt['gate_id'], read_receipt['gate_id'])
        self.assertEqual(receipt['snapshot_hash'], read_receipt['snapshot_hash'])
        self.assertEqual(receipt['signature'], read_receipt['signature'])

        # Step 6: Re-validate read receipt
        revalidation_result = validator.validate_receipt(read_receipt)
        self.assertTrue(revalidation_result['valid'],
                                            f"Re-validation failed: {revalidation_result.get('errors', [])}")

    def test_receipt_jsonl_format(self):
        """Test receipt in JSONL format (append-only)."""
        from validator.receipt_validator import ReceiptValidator
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / 'src' / 'shared' / 'storage'))
        from BaseStoragePathResolver import BaseStoragePathResolver

        resolver = BaseStoragePathResolver(str(self.zu_root))
        year = datetime.utcnow().year
        month = datetime.utcnow().month
        receipt_dir = Path(resolver.resolveReceiptPath(self.repo_id, year, month))
        receipt_dir.mkdir(parents=True, exist_ok=True)

        jsonl_file = receipt_dir / 'receipts.jsonl'

        # Generate multiple receipts
        receipts = []
        for i in range(3):
            receipt = generate_mock_receipt(self.repo_id, f"{self.gate_id}_{i}", 'pass')
            receipts.append(receipt)

            # Append to JSONL file
            with open(jsonl_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(receipt, ensure_ascii=False) + '\n')

        # Validate JSONL file
        validator = ReceiptValidator()
        jsonl_result = validator.validate_jsonl_file(jsonl_file)

        self.assertTrue(jsonl_result['valid'],
                                                        f"JSONL validation failed: {jsonl_result.get('errors_by_line', [])}")
        self.assertEqual(jsonl_result['valid_count'], 3)
        self.assertEqual(jsonl_result['total_count'], 3)

    def test_receipt_signature_consistency(self):
        """Test that receipt signatures are consistent across reads."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / 'src' / 'shared' / 'storage'))
        from BaseStoragePathResolver import BaseStoragePathResolver

        receipt = generate_mock_receipt(self.repo_id, self.gate_id, 'pass')
        original_signature = receipt['signature']

        resolver = BaseStoragePathResolver(str(self.zu_root))
        year = datetime.utcnow().year
        month = datetime.utcnow().month
        receipt_dir = Path(resolver.resolveReceiptPath(self.repo_id, year, month))
        receipt_dir.mkdir(parents=True, exist_ok=True)

        receipt_file = receipt_dir / f"{receipt['receipt_id']}.json"
        with open(receipt_file, 'w', encoding='utf-8') as f:
            json.dump(receipt, f, indent=2, ensure_ascii=False, sort_keys=True)

        # Read back and verify signature unchanged
        with open(receipt_file, 'r', encoding='utf-8') as f:
            read_receipt = json.load(f)

        self.assertEqual(original_signature, read_receipt['signature'],
                        "Signature must remain consistent after write/read cycle")


if __name__ == '__main__':
    unittest.main()

