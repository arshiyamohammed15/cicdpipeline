from __future__ import annotations
import pytest

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
    """Iterate Python files, skipping excluded directories and handling symlink issues."""
    import os
    visited = set()
    
    def should_skip_path(path: Path) -> bool:
        """Check if path should be skipped."""
        # Skip if path contains excluded directories
        if any(part in EXCLUDED_DIRS for part in path.parts):
            return True
        if path.name in EXCLUDED_FILES:
            return True
        return False
    
    # Use os.walk for better control over traversal and error handling
    try:
        for root, dirs, files in os.walk(repo_root, followlinks=False, onerror=lambda err: None):
            # Filter out excluded directories from dirs to prevent traversal
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
            
            root_path = Path(root)
            if should_skip_path(root_path):
                continue
                
            for file in files:
                if not file.endswith('.py'):
                    continue
                path = root_path / file
                try:
                    # Resolve symlinks and check for circular references
                    real_path = path.resolve()
                    if real_path in visited:
                        continue
                    visited.add(real_path)
                    
                    if should_skip_path(path):
                        continue
                    yield path
                except (OSError, RuntimeError):
                    # Skip paths that can't be resolved (circular symlinks, etc.)
                    continue
    except (OSError, RuntimeError) as e:
        # If os.walk itself fails, fall back to a simpler approach
        # Just skip this test if we can't traverse the directory tree
        import warnings
        warnings.warn(f"Could not traverse directory tree: {e}")
        return


@pytest.mark.unit
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
