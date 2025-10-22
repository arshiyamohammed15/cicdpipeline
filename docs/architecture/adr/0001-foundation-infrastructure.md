# ADR 0001 — Foundation and Infrastructure Baseline

- **Date:** 2025-10-21
- **Status:** Proposed
- **Deciders:** ZeroUI 2.0 Architecture Working Group
- **Technical Area:** Repository foundations, tooling, build and configuration management

## Context

ZeroUI 2.0 is currently a foundation-only codebase intended to enforce the product constitution without shipping end-user functionality yet. The repository already contains:

- A rich rule corpus defined in `ZeroUI2.0_Master_Constitution.md` that is meant to be the single source of truth.
- Python infrastructure for validation (`validator/`, `config/`) and a VS Code extension scaffold (`src/vscode-extension/`).
- Tooling collateral such as `pyproject.toml`, `requirements*.txt`, `.pre-commit-config.yaml`, and extensive documentation.

During the baseline assessment we identified systemic inconsistencies that threaten future development:

1. **Rule inventory drift.** The Markdown source (231 rules) disagrees with derived configuration counts (215) and public library claims (71) across `ZeroUI2.0_Master_Constitution.md`, `config/base_config.json`, and `validator/__init__.py`. This breaks the “single source of truth” promise and makes validation results unreliable.
2. **Test harness disabled.** `--collect-only` is part of the default pytest arguments (`pyproject.toml:127`), stopping test execution and hiding regressions and coverage signals.
3. **Dependency ambiguity.** Runtime dependencies include development-only tooling while `constraints.txt` and `requirements.lock` disagree on multiple transitive versions (for example `smmap`, `typing-inspection`).
4. **Unstable import boundaries.** Multiple modules mutate `sys.path` to climb above the repository root, making the validator sensitive to sibling directories and undermining packaging.
5. **Cross-platform developer friction.** Several pre-commit hooks rely on GNU utilities (`bash`, `grep`) without documenting the requirement, and some hook definitions are duplicated or under-specified.
6. **Versioning and licensing gaps.** `pyproject.toml` reports version `2.0.0` while `validator/__init__.py` exports `1.0.0`; an MIT licence is advertised but no `LICENSE` file exists.

Without decisive guardrails, later functionality will inherit these mismatches, increasing operational risk and maintenance cost.

## Decision

We establish the following foundation principles and commitments:

### 1. Constitution Source of Truth Enforcement
- Treat `ZeroUI2.0_Master_Constitution.md` as the *only* authoring surface for rules.
- Generate **all** derived artefacts (SQLite, JSON exports, enabled/disabled configuration, documentation snippets, test fixtures) from the Markdown using an automated command (`enhanced_cli.py --rebuild-from-markdown`) that becomes part of the build pipeline.
- Block merges when rule counts or metadata extracted from the Markdown diverge from the generated artefacts (compare counts, identifiers, priorities, and enabled flags).
- Embed a documentation quality pipeline in CI that:
  - Builds the documentation set (Markdown/Sphinx) to catch structural errors early.
  - Runs link checking across internal anchors and external URLs.
  - Maintains versioned documentation snapshots so generated rule snippets align with released validator versions.

### 2. Toolchain and Dependency Baseline
- Set Python **3.11** as the minimum supported interpreter in code and documentation. Remove contradictory guidance (for example `README.md:19`, `LOCAL_DEPLOYMENT.md:8`) or uplift the codebase if 3.9 compatibility is required.
- Split dependencies into:
  - Runtime package requirements (library execution paths only).
  - Development extras and tooling (linters, formatters, test runners, type stubs, pre-commit).
- Maintain a single machine-generated lock artefact (`constraints.txt` or `requirements.lock`, not both) and enforce consistency with continuous integration.

### 3. Testing and Continuous Verification
- Remove `--collect-only` from default pytest arguments and introduce a CI job that executes the full test suite with coverage enforcement.
- Add a smoke test that fails when test discovery yields zero executed tests.
- Publish the pytest invocation as the canonical validation command in documentation.

### 4. Import and Packaging Hygiene
- Replace ad-hoc `sys.path.insert` logic (`validator/core.py:22`, `validator/optimized_core.py:27`, `config/constitution/config_manager.py:23-30`) with proper Python packaging:
  - Install the project in editable mode during development (`pip install -e .`).
  - Ensure all internal modules resolve via the `zeroui_2` namespace (final name to be set as part of packaging).
- Provide a CLI entry point (`[project.scripts]` in `pyproject.toml`) instead of relying on top-level scripts (`enhanced_cli.py`).

### 5. Developer Workflow Portability
- Review `.pre-commit-config.yaml` to eliminate duplicate hooks and platform-specific assumptions:
  - Replace shell pipelines that rely on GNU utilities with cross-platform Python implementations or guard them behind documented prerequisites.
  - Fix misconfigured hooks (`check-commit-msg`) by supplying required arguments or remove them until configured correctly.
- Document the expected developer environment (shell requirements, Node.js for the VS Code extension, optional PowerShell tooling).

### 6. Versioning and Legal Metadata
- Align the project version across metadata (`pyproject.toml:7`, `validator/__init__.py:12`) and adopt Semantic Versioning for the foundation.
- Add the MIT `LICENSE` file referenced by classifiers and ensure packaging includes it.
- Track ADRs in `docs/architecture/adr` to provide traceable design history going forward.

### 7. Cross-Component Integration
- Treat the VS Code extension as a first-class consumer of the validator package.
  - Define how the extension depends on the packaged validator (embedded wheel, shared virtual environment, or API calls) and automate that integration.
  - Update extension tooling to respect the runtime/dev dependency split and surface drift (e.g., fail builds when the extension pins an outdated validator version).
- Publish migration notes for extension maintainers whenever packaging or CLI entry points change, so UI surfaces stay aligned with backend validation.

## Rationale

- **Integrity of rule validation.** Enforcing a single authoritative source prevents silent drift between documentation and executable logic, ensuring that fail/pass outcomes remain defensible.
- **Reproducibility.** Tight dependency scoping and a consistent interpreter baseline are prerequisites for deterministic builds and reliable CI.
- **Guarding quality gates.** Running tests and coverage on every change is cheaper than debugging regressions discovered weeks later.
- **Packaging correctness.** Proper module resolution eliminates fragile environment-dependent behaviour and is mandatory for downstream consumption (pip packages, Docker images, internal tooling).
- **Developer inclusivity.** Cross-platform defaults reduce onboarding cost and prevent class-of-user lockouts, including VS Code extension maintainers who depend on the validator distribution.
- **Governance and compliance.** Correct versioning and licensing are legal and operational necessities; ADR tracking preserves institutional memory.

## Implementation Plan

1. **Rule pipeline hardening**
   - Implement or update the Markdown extraction routine so that it regenerates `config/base_config.json`, SQLite, JSON caches, and any derived enumerations.
   - Add CI checks: `enhanced_cli.py --verify-consistency` (or equivalent) plus count assertions.
   - Define failure handling for the regeneration workflow: categorise malformed Markdown as authoring errors (blocking merges with actionable feedback) and infrastructure issues as system errors (with structured logging, retries where safe, and automatic rollback of partially written artefacts).
   - Ensure regeneration jobs leave the repository in a consistent state by cleaning or restoring intermediate files when failures occur.
2. **Toolchain alignment**
   - Update documentation to state Python 3.11 minimum, or raise code compatibility to match existing documentation.
   - Refactor dependency declarations (runtime vs dev extras) and remove redundant lock files. Add a job that fails when the lock and manifest drift.
   - Add documentation build and link-check stages to CI and record the chosen documentation versioning strategy (e.g., per-release snapshots).
3. **Testing pipeline**
   - Update `pyproject.toml` to remove `--collect-only`.
   - Add scripts/CI tasks for `pytest --cov` and enforce coverage thresholds.
4. **Packaging refactor**
   - Introduce a project package (e.g., `src/zeroui_validator/__init__.py`) and move CLI entry point into the package.
   - Remove `sys.path` mutations and update imports accordingly.
   - Document and automate how the VS Code extension consumes the packaged validator, including dependency pinning and build-time verification.
5. **Pre-commit and workflow updates**
   - Replace shell-based hooks with Python equivalents or vendor required tools via pre-commit’s language mechanisms.
   - Document workflow prerequisites in `README.md` or `CONTRIBUTING.md`.
6. **Metadata corrections**
   - Synchronise version constants and add the missing `LICENSE`.
   - Register ADR index (`docs/architecture/adr/README.md`) for discoverability (future work).

Implementation should proceed in small, reviewable pull requests to limit disruption. Each milestone must include corresponding documentation updates and automated checks.

## Consequences

### Positive
- Deterministic rule outputs, reducing the risk of shipping incorrect validations.
- Predictable developer onboarding due to explicit environment requirements.
- Stronger test guarantees and observability into regression risk.
- A maintainable packaging story that supports reuse, deployment, and distribution.
- Clear governance artefacts (ADR, licence, version alignment) supporting compliance and audits.

### Negative / Risks
- Short-term increase in engineering effort to refactor imports and dependency declarations.
- CI may initially fail after enabling tests and consistency checks, requiring remediation work.
- Packaging changes can break downstream scripts; coordination and migration guides are necessary.

### Risk Mitigations
- Stage refactors with feature flags or compatibility shims where feasible.
- Communicate upcoming enforcement (e.g., new CI requirements) ahead of activation.
- Provide upgrade notes and scripts for developers when the dependency structure changes.

## Alternatives Considered

1. **Maintain the status quo.** Rejected because it preserves broken tests, dependency drift, and inconsistent rule sources—risks far outweigh the convenience.
2. **Adopt Markdown-only validation without derived artefacts.** Rejected because runtime components require fast lookups and precomputed indices; regeneration offers both performance and consistency.
3. **Loosen platform expectations by mandating Git Bash or WSL.** Rejected to keep the workflow inclusive for Windows-first environments and avoid hard platform requirements.

## Validation

The decision is considered implemented when:

- CI executes full pytest suites (without `--collect-only`) and enforces coverage ≥ 80% as configured.
- `enhanced_cli.py --verify-consistency` (or successor) passes and rule counts match across Markdown, configuration, JSON, and SQLite.
- Package metadata (`pyproject.toml`, public API, distribution artefacts) align on version and include the MIT licence.
- Pre-commit runs succeed on Windows and Unix without manual shell installations beyond documented prerequisites.
- README (and other onboarding docs) reflect the final interpreter baseline and dependency split.

## Future Work

- Automate ADR index generation and include links in `README.md`.
- Define a release governance process (version bump workflow, changelog, signing policy).
- Evaluate packaging for the PowerShell scaffolding (`storage-scripts/tools/scaffold/zero_ui_scaffold.ps1`) to ensure parity with Python tooling.
- Extend CI with cross-component smoke tests that install the VS Code extension against the packaged validator to guard against integration regressions.
- Integrate the documentation build/link-check pipeline into the developer workflow (pre-commit or make targets) once performance budgets are understood.
- Introduce schema validation for GSMD snapshots and integrate it into the continuous build once the rule pipeline is stabilised.

---

*This ADR documents the non-functional foundation decisions and will guide subsequent functional work. Revisit it if interpreter requirements, packaging strategy, or rule governance materially change.*
