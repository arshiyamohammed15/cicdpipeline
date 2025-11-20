# Manual Test Artifacts

This directory quarantines files that intentionally violate formatting or lint
rules so the pre-commit hook workflow can be exercised safely.  Tooling that
walks `tests/` should skip `tests/manual/` altogether.

Current contents:

- `test_commit_consistency.py` – deliberately misformatted module used to
  confirm the non-blocking pre-commit hooks still auto-fix staged files.
- `commit_consistency_test.txt` – companion text file describing the manual
  verification steps for the same workflow.

If you add new manual artefacts, keep them here and document the rationale so
automated test discovery never trips over them.

