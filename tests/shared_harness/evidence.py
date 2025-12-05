from __future__ import annotations
"""
Evidence pack builder for compliance and audit requirements.
"""


import json
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class EvidencePackBuilder:
    """Builds timestamped evidence packs containing test results, receipts, and configs."""

    def __init__(self, output_dir: Path | str = "artifacts") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.receipts: List[Dict[str, Any]] = []
        self.config_snapshots: List[Dict[str, Any]] = []
        self.metrics: List[Dict[str, Any]] = []

    def add_receipt(self, receipt: Dict[str, Any]) -> None:
        """Add an ERIS receipt to the evidence pack."""
        self.receipts.append(receipt)

    def add_config_snapshot(self, config: Dict[str, Any], name: str) -> None:
        """Add a configuration snapshot (policy, tenant config, etc.)."""
        self.config_snapshots.append({"name": name, "config": config})

    def add_metrics(self, metrics: Dict[str, Any]) -> None:
        """Add performance or operational metrics."""
        self.metrics.append(metrics)

    def build(self, module_name: str, test_suite: str) -> Path:
        """Generate a timestamped evidence pack ZIP file."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        zip_path = self.output_dir / f"{module_name}_{test_suite}_{timestamp}.zip"

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            manifest = {
                "module": module_name,
                "test_suite": test_suite,
                "timestamp": timestamp,
                "receipt_count": len(self.receipts),
                "config_count": len(self.config_snapshots),
                "metrics_count": len(self.metrics),
            }
            zf.writestr("manifest.json", json.dumps(manifest, indent=2))

            if self.receipts:
                zf.writestr("receipts.jsonl", "\n".join(json.dumps(r) for r in self.receipts))

            if self.config_snapshots:
                zf.writestr("configs.json", json.dumps(self.config_snapshots, indent=2))

            if self.metrics:
                zf.writestr("metrics.json", json.dumps(self.metrics, indent=2))

        return zip_path

