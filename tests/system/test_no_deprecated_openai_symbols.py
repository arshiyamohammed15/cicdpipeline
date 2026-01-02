from __future__ import annotations

from pathlib import Path


DEPRECATED_TOKENS = (
    "openai.Edit",
    "openai.ChatCompletion",
    "openai.Completion",
    "openai.Embedding",
    "openai.Image",
    "openai.Audio",
    "openai.Moderation",
)

EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "artifacts",
    "dist",
    "build",
    "__pycache__",
    ".pytest_cache",
}
EXCLUDED_FILES = {
    "test_no_deprecated_openai_symbols.py",
}


def _iter_python_files(repo_root: Path):
    for path in repo_root.rglob("*.py"):
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        if path.name in EXCLUDED_FILES:
            continue
        yield path


def test_no_deprecated_openai_symbols():
    repo_root = Path(__file__).resolve().parents[2]
    hits = []
    for path in _iter_python_files(repo_root):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for line_no, line in enumerate(text.splitlines(), start=1):
            for token in DEPRECATED_TOKENS:
                if token in line:
                    hits.append(f"{path}:{line_no}: {line.strip()}")

    assert not hits, "Deprecated OpenAI symbols found:\n" + "\n".join(hits)
