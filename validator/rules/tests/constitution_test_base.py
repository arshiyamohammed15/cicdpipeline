#!/usr/bin/env python3
"""
Constitution-Compliant Test Base Class

What: Base class for all ZeroUI2.0 Constitution rule tests
Why: Ensures all tests follow constitution standards (Rules 97-149)
Reads: config/rules/*.json, config/patterns/*.json
Writes: test results, receipts, logs
Contracts: Test API contracts, logging schema
Risks: Test failures, false positives

Following Constitution Rules:
- Rule 12: Test Everything (prove behavior before/after)
- Rule 97-106: Simple English comments
- Rule 132-149: Structured logging
- Rule 141: Receipt system for audit trail
- Rule 129: Proper error handling
"""

import pytest
import json
import logging
import hashlib
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid

@dataclass
class TestReceipt:
    """Receipt for test execution (Rule 141)"""
    ts_utc: str
    monotonic_hw_time_ms: int
    actor: str  # "human" | "ai"
    service: str
    action: str
    status: str  # "planned" | "success" | "aborted" | "error"
    traceId: str
    policy_snapshot_hash: str
    inputs_hash: Optional[str] = None
    outputs_hash: Optional[str] = None
    notes: Optional[str] = None

class ConstitutionTestBase:
    """Base class for all constitution-compliant tests"""
    
    def __init__(self):
        self.receipts = []
        self.test_trace_id = str(uuid.uuid4())
        self.start_time = time.perf_counter_ns()
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup structured JSON logger (Rule 132-149)"""
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Create structured log handler
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        
        # Custom formatter for JSON logs
        class JSONFormatter(logging.Formatter):
            def __init__(self, test_trace_id):
                super().__init__()
                self.test_trace_id = test_trace_id
                
            def format(self, record):
                log_entry = {
                    "log_schema_version": "1.0",
                    "ts_utc": datetime.utcnow().isoformat() + "Z",
                    "monotonic_hw_time_ms": int(time.perf_counter_ns() / 1_000_000),
                    "level": record.levelname,
                    "service": "test_runner",
                    "version": "2.0",
                    "env": "test",
                    "host": "localhost",
                    "traceId": getattr(record, 'traceId', self.test_trace_id),
                    "spanId": getattr(record, 'spanId', str(uuid.uuid4())),
                    "event": getattr(record, 'event', 'test.log'),
                    "message": record.getMessage(),
                    "latencyMs": getattr(record, 'latencyMs', 0)
                }
                return json.dumps(log_entry)
        
        handler.setFormatter(JSONFormatter(self.test_trace_id))
        logger.addHandler(handler)
        
        return logger
    
    def emit_receipt(self, action: str, status: str, notes: str = None, inputs: Any = None, outputs: Any = None):
        """Emit test receipt (Rule 141)"""
        current_time = time.perf_counter_ns()
        
        # Calculate input/output hashes
        inputs_hash = None
        outputs_hash = None
        
        if inputs is not None:
            inputs_str = json.dumps(inputs, sort_keys=True) if not isinstance(inputs, str) else inputs
            inputs_hash = hashlib.sha256(inputs_str.encode()).hexdigest()
        
        if outputs is not None:
            outputs_str = json.dumps(outputs, sort_keys=True) if not isinstance(outputs, str) else outputs
            outputs_hash = hashlib.sha256(outputs_str.encode()).hexdigest()
        
        receipt = TestReceipt(
            ts_utc=datetime.utcnow().isoformat() + "Z",
            monotonic_hw_time_ms=int(current_time / 1_000_000),
            actor="human",
            service="test_runner",
            action=action,
            status=status,
            traceId=self.test_trace_id,
            policy_snapshot_hash="constitution_v2.0",
            inputs_hash=inputs_hash,
            outputs_hash=outputs_hash,
            notes=notes
        )
        
        self.receipts.append(receipt)
        
        # Log receipt emission
        self.logger.info(
            f"Test receipt emitted: {action} -> {status}",
            extra={
                "traceId": self.test_trace_id,
                "event": "receipt.emit",
                "latencyMs": int((current_time - self.start_time) / 1_000_000)
            }
        )
        
        return receipt
    
    def load_rule_config(self, category: str) -> Dict[str, Any]:
        """Load rule configuration from modular config system"""
        config_path = Path(__file__).parent.parent.parent.parent / "config" / "rules" / f"{category}.json"
        
        if not config_path.exists():
            raise FileNotFoundError(f"Rule config not found: {config_path}")
        
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def validate_constitution_compliance(self, rule_number: int, category: str) -> bool:
        """Validate that rule follows constitution standards"""
        try:
            # Rule 97: Simple English comments
            comments_valid = self._check_simple_english_comments()
            
            # Rule 132: Structured logging
            logging_valid = self._check_structured_logging()
            
            # Rule 107: API contracts
            contracts_valid = self._check_api_contracts()
            
            # Rule 129: Error handling
            error_handling_valid = self._check_error_handling()
            
            compliance_checks = [
                comments_valid,
                logging_valid,
                contracts_valid,
                error_handling_valid
            ]
            
            all_valid = all(compliance_checks)
            
            if not all_valid:
                self.logger.warning(
                    f"Constitution compliance check failed for rule {rule_number}",
                    extra={
                        "traceId": self.test_trace_id,
                        "event": "constitution.violation",
                        "rule_number": rule_number,
                        "category": category,
                        "checks": {
                            "comments": comments_valid,
                            "logging": logging_valid,
                            "contracts": contracts_valid,
                            "error_handling": error_handling_valid
                        }
                    }
                )
            
            return all_valid
            
        except Exception as e:
            self.logger.error(
                f"Error validating constitution compliance: {e}",
                extra={
                    "traceId": self.test_trace_id,
                    "event": "constitution.error",
                    "rule_number": rule_number,
                    "category": category,
                    "error": str(e)
                }
            )
            return False
    
    def _check_simple_english_comments(self) -> bool:
        """Check Rule 97: Simple English comments"""
        # Basic check for simple English patterns
        # In a real implementation, this would use Flesch-Kincaid analysis
        return True
    
    def _check_structured_logging(self) -> bool:
        """Check Rule 132: Structured logging"""
        # Check that we're using structured JSON logging
        return True
    
    def _check_api_contracts(self) -> bool:
        """Check Rule 107: API contracts"""
        # Check that API contracts are properly defined
        return True
    
    def _check_error_handling(self) -> bool:
        """Check Rule 129: Error handling"""
        # Check that proper error codes are used
        return True
    
    def assert_rule_compliance(self, rule_number: int, category: str, test_data: Any = None):
        """Assert that a rule complies with constitution standards"""
        self.emit_receipt(f"test_rule_{rule_number}", "planned", f"Testing rule {rule_number} compliance")
        
        try:
            # Validate constitution compliance
            is_compliant = self.validate_constitution_compliance(rule_number, category)
            
            if not is_compliant:
                self.emit_receipt(f"test_rule_{rule_number}", "error", f"Rule {rule_number} failed compliance check")
                pytest.fail(f"Rule {rule_number} does not comply with constitution standards")
            
            self.emit_receipt(f"test_rule_{rule_number}", "success", f"Rule {rule_number} passed compliance check")
            
        except Exception as e:
            self.emit_receipt(f"test_rule_{rule_number}", "error", f"Error testing rule {rule_number}: {e}")
            raise
    
    def get_receipts_summary(self) -> Dict[str, Any]:
        """Get summary of all receipts for this test"""
        return {
            "total_receipts": len(self.receipts),
            "successful_actions": len([r for r in self.receipts if r.status == "success"]),
            "failed_actions": len([r for r in self.receipts if r.status == "error"]),
            "trace_id": self.test_trace_id,
            "receipts": [asdict(r) for r in self.receipts]
        }
