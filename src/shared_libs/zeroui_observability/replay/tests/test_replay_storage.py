"""
Tests for ReplayStorage.

OBS-15: Replay Bundle Storage tests.
"""

import json
import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

from ..replay_bundle_builder import ReplayBundle
from ..replay_storage import ReplayStorage


class TestReplayStorage(unittest.TestCase):
    """Test ReplayStorage."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.storage = ReplayStorage(zu_root=self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_store_success(self):
        """Test storing replay bundle."""
        bundle = ReplayBundle(
            replay_id="replay_001",
            trigger_event_id="event_001",
            included_event_ids=["event_001", "event_002"],
            checksum="a" * 64,
            storage_ref="path/to/bundle.jsonl",
            trace_id="a" * 32,
            created_at=datetime.now(timezone.utc),
        )

        bundle_payload = {"events": []}

        storage_path = self.storage.store(
            bundle,
            bundle_payload,
            tenant_id="tenant_001",
        )

        # Verify file was created
        self.assertTrue(Path(storage_path).exists())

        # Verify content
        with open(storage_path, "r", encoding="utf-8") as f:
            content = json.loads(f.read())
            self.assertEqual(content["replay_id"], "replay_001")
            self.assertEqual(content["trace_id"], "a" * 32)

    def test_store_missing_tenant_id(self):
        """Test storing bundle without tenant_id."""
        bundle = ReplayBundle(
            replay_id="replay_001",
            trigger_event_id="event_001",
            included_event_ids=["event_001"],
            checksum="a" * 64,
            storage_ref="path/to/bundle.jsonl",
        )

        bundle_payload = {"events": []}

        with self.assertRaises(ValueError):
            self.storage.store(bundle, bundle_payload, tenant_id="")

    def test_retrieve_success(self):
        """Test retrieving replay bundle."""
        # Store bundle first
        bundle = ReplayBundle(
            replay_id="replay_001",
            trigger_event_id="event_001",
            included_event_ids=["event_001"],
            checksum="a" * 64,
            storage_ref="path/to/bundle.jsonl",
            trace_id="a" * 32,
            created_at=datetime.now(timezone.utc),
        )

        bundle_payload = {"events": []}
        self.storage.store(bundle, bundle_payload, tenant_id="tenant_001")

        # Retrieve bundle
        retrieved = self.storage.retrieve("replay_001", tenant_id="tenant_001")

        # Verify retrieved bundle
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["replay_id"], "replay_001")
        self.assertEqual(retrieved["trace_id"], "a" * 32)

    def test_retrieve_not_found(self):
        """Test retrieving non-existent bundle."""
        retrieved = self.storage.retrieve("nonexistent", tenant_id="tenant_001")
        self.assertIsNone(retrieved)


if __name__ == "__main__":
    unittest.main()
