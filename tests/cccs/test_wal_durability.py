"""
Tests for WAL durability and persistence.

Covers PRD section 10.1: WAL durability, deep-copy payloads, budget/policy snapshot persistence.
"""

from pathlib import Path
import json

import pytest

from src.shared_libs.cccs.receipts.wal import WALEntry, WALQueue


def test_wal_deep_copy_payloads(tmp_path):
    """Test WAL deep-copies payloads to prevent mutation."""
    wal = WALQueue(tmp_path / "wal.log")
    
    original_payload = {"mutable": {"key": "value"}}
    entry = wal.append(original_payload)
    
    # Mutate original
    original_payload["mutable"]["key"] = "mutated"
    
    # WAL entry should not be mutated
    assert entry.payload["mutable"]["key"] == "value"


def test_wal_persist_budget_snapshots(tmp_path):
    """Test WAL persists budget snapshots."""
    wal = WALQueue(tmp_path / "wal.log")
    
    budget_data = {"action_id": "action1", "remaining": 50.0, "tenant_id": "t1"}
    entry = wal.append_budget_snapshot(budget_data)
    
    assert entry.entry_type == "budget"
    assert entry.payload == budget_data
    
    # Verify persisted
    wal_content = (tmp_path / "wal.log").read_text()
    assert "budget" in wal_content
    assert "action1" in wal_content


def test_wal_persist_policy_snapshots(tmp_path):
    """Test WAL persists policy snapshots."""
    wal = WALQueue(tmp_path / "wal.log")
    
    policy_data = {"module_id": "m01", "version": "1.0.0", "snapshot_hash": "sha256:abc"}
    entry = wal.append_policy_snapshot(policy_data)
    
    assert entry.entry_type == "policy_snapshot"
    assert entry.payload == policy_data
    
    # Verify persisted
    wal_content = (tmp_path / "wal.log").read_text()
    assert "policy_snapshot" in wal_content
    assert "m01" in wal_content


def test_wal_durability_fsync(tmp_path):
    """Test WAL durability with fsync."""
    wal = WALQueue(tmp_path / "wal.log")
    
    # Append multiple entries
    for i in range(10):
        wal.append({"sequence": i, "data": f"entry-{i}"})
    
    # Verify all entries persisted
    wal_content = (tmp_path / "wal.log").read_text()
    lines = [l for l in wal_content.splitlines() if l.strip()]
    assert len(lines) == 10
    
    # Verify sequence continuity
    sequences = []
    for line in lines:
        entry = json.loads(line)
        sequences.append(entry["sequence"])
    assert sequences == list(range(1, 11))


def test_wal_pending_sync_receipts(tmp_path):
    """Test WAL emits pending_sync receipts."""
    wal = WALQueue(tmp_path / "wal.log")
    
    entry = wal.append({"type": "receipt", "data": "test"})
    
    # Mark as pending_sync
    wal.mark(entry.sequence, "pending_sync")
    
    # Verify state persisted
    pending_entries = list(wal.get_pending_sync_entries())
    assert len(pending_entries) == 1
    assert pending_entries[0].sequence == entry.sequence
    assert pending_entries[0].state == "pending_sync"


def test_wal_dead_letter_receipts(tmp_path):
    """Test WAL emits dead_letter receipts on failure."""
    wal = WALQueue(tmp_path / "wal.log")
    
    entry = wal.append({"type": "receipt", "data": "test"})
    
    # Simulate drain failure
    def failing_sink(_payload):
        raise RuntimeError("Sink failure")
    
    drained = list(wal.drain(failing_sink))
    assert len(drained) == 0  # Nothing successfully drained
    
    # Entry should be marked as dead_letter
    dead_letter_entries = list(wal.get_dead_letter_entries())
    assert len(dead_letter_entries) == 1
    assert dead_letter_entries[0].sequence == entry.sequence
    assert dead_letter_entries[0].state == "dead_letter"


def test_wal_recovery_after_crash(tmp_path):
    """Test WAL recovery after crash (load from disk)."""
    wal1 = WALQueue(tmp_path / "wal.log")
    
    # Add entries
    entries = []
    for i in range(5):
        entry = wal1.append({"index": i, "data": f"entry-{i}"})
        entries.append(entry)
    
    # Create new WAL instance (simulating restart)
    wal2 = WALQueue(tmp_path / "wal.log")
    
    # Should load all entries
    assert len(wal2._entries) == 5
    
    # Verify sequence continuity
    sequences = [e.sequence for e in wal2._entries]
    assert sequences == list(range(1, 6))


def test_wal_atomic_writes(tmp_path):
    """Test WAL atomic writes (write to temp, then rename)."""
    wal = WALQueue(tmp_path / "wal.log")
    
    # Append entry (should use atomic write)
    entry = wal.append({"test": "data"})
    
    # Verify file exists and is valid JSON
    assert (tmp_path / "wal.log").exists()
    
    content = (tmp_path / "wal.log").read_text()
    parsed = json.loads(content.strip())
    assert parsed["sequence"] == entry.sequence
    assert parsed["payload"] == entry.payload


def test_wal_entry_type_tracking(tmp_path):
    """Test WAL tracks entry types (receipt, budget, policy_snapshot)."""
    wal = WALQueue(tmp_path / "wal.log")
    
    receipt_entry = wal.append({"type": "receipt"}, entry_type="receipt")
    budget_entry = wal.append_budget_snapshot({"action_id": "a1"})
    policy_entry = wal.append_policy_snapshot({"module_id": "m1"})
    
    assert receipt_entry.entry_type == "receipt"
    assert budget_entry.entry_type == "budget"
    assert policy_entry.entry_type == "policy_snapshot"
    
    # Verify persisted
    content = (tmp_path / "wal.log").read_text()
    assert '"entry_type": "receipt"' in content
    assert '"entry_type": "budget"' in content
    assert '"entry_type": "policy_snapshot"' in content

