#!/usr/bin/env python3
"""
Test Suite for Receipt Validator

Tests validator/receipt_validator.py functionality:
- Receipt structure validation
- Timestamp validation
- Decision status validation
- Policy references validation
- Signature validation
- JSONL file validation
"""

import sys
import unittest
import json
import tempfile
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from validator.receipt_validator import ReceiptValidator


class TestReceiptValidator(unittest.TestCase):
    """Test ReceiptValidator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = ReceiptValidator()
    
    def test_initialization(self):
        """Test ReceiptValidator initializes correctly."""
        self.assertIsNotNone(self.validator)
        self.assertIsNotNone(self.validator.REQUIRED_FIELDS)
        self.assertIsNotNone(self.validator.VALID_STATUSES)
    
    def create_valid_receipt(self) -> dict:
        """Create a valid receipt for testing."""
        now = datetime.now(timezone.utc)
        return {
            'receipt_id': 'test-receipt-123',
            'gate_id': 'pr-size',
            'policy_version_ids': ['v1.0.0'],
            'snapshot_hash': 'sha256:' + 'a' * 64,
            'timestamp_utc': now.isoformat().replace('+00:00', 'Z'),
            'timestamp_monotonic_ms': int(now.timestamp() * 1000),
            'decision': {
                'status': 'pass',
                'rationale': 'Test decision'
            },
            'signature': 'test-signature-123'
        }
    
    def test_validate_valid_receipt(self):
        """Test validation of valid receipt."""
        receipt = self.create_valid_receipt()
        result = self.validator.validate_receipt(receipt)
        
        self.assertTrue(result['valid'])
        self.assertEqual(len(result['errors']), 0)
        self.assertEqual(result['receipt_id'], 'test-receipt-123')
    
    def test_validate_receipt_structure_missing_fields(self):
        """Test validation detects missing required fields."""
        receipt = {'receipt_id': 'test'}  # Missing most fields
        result = self.validator.validate_receipt_structure(receipt)
        
        # Should detect missing fields
        self.assertGreater(len(result), 0)
        self.assertIn('Missing required field', result[0])
    
    def test_validate_timestamps_valid(self):
        """Test timestamp validation with valid timestamps."""
        receipt = {
            'timestamp_utc': '2024-01-01T00:00:00Z',
            'timestamp_monotonic_ms': 1704067200000
        }
        result = self.validator.validate_timestamps(receipt)
        
        self.assertEqual(len(result), 0)
    
    def test_validate_timestamps_invalid_utc(self):
        """Test timestamp validation detects invalid UTC format."""
        receipt = {
            'timestamp_utc': '2024-01-01T00:00:00',  # Missing Z
            'timestamp_monotonic_ms': 1704067200000
        }
        result = self.validator.validate_timestamps(receipt)
        
        self.assertGreater(len(result), 0)
        self.assertIn('UTC', result[0])
    
    def test_validate_timestamps_invalid_monotonic(self):
        """Test timestamp validation detects invalid monotonic time."""
        receipt = {
            'timestamp_utc': '2024-01-01T00:00:00Z',
            'timestamp_monotonic_ms': 'not-a-number'
        }
        result = self.validator.validate_timestamps(receipt)
        
        self.assertGreater(len(result), 0)
        self.assertIn('monotonic', result[0].lower())
    
    def test_validate_decision_status_valid(self):
        """Test decision status validation with valid status."""
        for status in ['pass', 'warn', 'soft_block', 'hard_block']:
            receipt = {'decision': {'status': status}}
            result = self.validator.validate_decision_status(receipt)
            self.assertEqual(len(result), 0, f"Status {status} should be valid")
    
    def test_validate_decision_status_invalid(self):
        """Test decision status validation detects invalid status."""
        receipt = {'decision': {'status': 'invalid_status'}}
        result = self.validator.validate_decision_status(receipt)
        
        self.assertGreater(len(result), 0)
        self.assertIn('Invalid decision status', result[0])
    
    def test_validate_decision_status_string_format(self):
        """Test decision status validation with string format."""
        receipt = {'decision': 'pass'}
        result = self.validator.validate_decision_status(receipt)
        
        self.assertEqual(len(result), 0)
    
    def test_validate_policy_references_valid(self):
        """Test policy references validation with valid values."""
        receipt = {
            'snapshot_hash': 'sha256:' + 'a' * 64,
            'policy_version_ids': ['v1.0.0', 'v1.0.1']
        }
        result = self.validator.validate_policy_references(receipt)
        
        self.assertEqual(len(result), 0)
    
    def test_validate_policy_references_invalid_hash(self):
        """Test policy references validation detects invalid hash format."""
        receipt = {
            'snapshot_hash': 'invalid-hash',
            'policy_version_ids': ['v1.0.0']
        }
        result = self.validator.validate_policy_references(receipt)
        
        self.assertGreater(len(result), 0)
        self.assertIn('sha256', result[0])
    
    def test_validate_policy_references_empty_version_ids(self):
        """Test policy references validation detects empty version IDs."""
        receipt = {
            'snapshot_hash': 'sha256:' + 'a' * 64,
            'policy_version_ids': []
        }
        result = self.validator.validate_policy_references(receipt)
        
        self.assertGreater(len(result), 0)
        self.assertIn('empty', result[0])
    
    def test_validate_signature_missing(self):
        """Test signature validation detects missing signature."""
        receipt = {}
        result = self.validator.validate_signature(receipt)
        
        self.assertGreater(len(result), 0)
        self.assertIn('signature', result[0])
    
    def test_validate_signature_empty(self):
        """Test signature validation detects empty signature."""
        receipt = {'signature': ''}
        result = self.validator.validate_signature(receipt)
        
        self.assertGreater(len(result), 0)
        self.assertIn('empty', result[0])
    
    def test_validate_jsonl_file_valid(self):
        """Test JSONL file validation with valid file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            receipt1 = self.create_valid_receipt()
            receipt1['receipt_id'] = 'receipt-1'
            receipt2 = self.create_valid_receipt()
            receipt2['receipt_id'] = 'receipt-2'
            
            f.write(json.dumps(receipt1) + '\n')
            f.write(json.dumps(receipt2) + '\n')
            f.flush()
            
            result = self.validator.validate_jsonl_file(Path(f.name))
            
            self.assertTrue(result['valid'])
            self.assertEqual(result['valid_count'], 2)
            self.assertEqual(result['total_count'], 2)
            self.assertEqual(len(result['errors_by_line']), 0)
    
    def test_validate_jsonl_file_invalid_json(self):
        """Test JSONL file validation detects invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('not valid json\n')
            f.flush()
            
            result = self.validator.validate_jsonl_file(Path(f.name))
            
            self.assertFalse(result['valid'])
            self.assertGreater(len(result['errors_by_line']), 0)
            self.assertIn('Invalid JSON', result['errors_by_line'][0]['errors'][0])
    
    def test_validate_jsonl_file_missing_file(self):
        """Test JSONL file validation handles missing file."""
        result = self.validator.validate_jsonl_file(Path('/nonexistent/file.jsonl'))
        
        self.assertFalse(result['valid'])
        self.assertIn('error', result)


class TestReceiptValidatorEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = ReceiptValidator()
    
    def test_validate_receipt_all_errors(self):
        """Test validation catches all types of errors."""
        receipt = {}  # Empty receipt - should have many errors
        result = self.validator.validate_receipt(receipt)
        
        self.assertFalse(result['valid'])
        self.assertGreater(len(result['errors']), 5)  # Should have multiple errors
    
    def test_validate_timestamps_negative_monotonic(self):
        """Test timestamp validation detects negative monotonic time."""
        receipt = {
            'timestamp_utc': '2024-01-01T00:00:00Z',
            'timestamp_monotonic_ms': -1
        }
        result = self.validator.validate_timestamps(receipt)
        
        self.assertGreater(len(result), 0)
        self.assertIn('non-negative', result[0])


if __name__ == '__main__':
    unittest.main()

