import json
import os
from pathlib import Path
from typing import Any, Dict


def _log_path(filename: str) -> Path:
    base = Path(os.getenv("PM_AUDIT_LOG_DIR", "artifacts/audit/logs"))
    base.mkdir(parents=True, exist_ok=True)
    return base / filename


def append_record(filename: str, record: Dict[str, Any]) -> Path:
    path = _log_path(filename)
    line = json.dumps(record, sort_keys=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
    return path
