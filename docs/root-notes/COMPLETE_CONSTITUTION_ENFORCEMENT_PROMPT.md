# ZeroUI Constitution Enforcement Prompt
_Generated via `python scripts/ci/render_constitution_prompt.py -o docs/root-notes/COMPLETE_CONSTITUTION_ENFORCEMENT_PROMPT.md`._

You must validate every prompt against **all 414 enabled rules (415 total)** defined in `docs/constitution/*.json` before generating any code or documentation.

## Required Workflow
1. Load the latest rule definitions from the JSON source of truth.
2. Evaluate the incoming prompt against every enabled rule.
3. If any rule is violated, stop immediately and return `ERROR:CONSTITUTION_VIOLATION - <Rule ID>: <Rule Title>`.
4. Only proceed with generation when **zero** violations are detected.

## Coverage Expectations by Category
- AI & CODE GENERATION RULES: 12 enabled / 12 total rules enforceable.
- AI Generation: 6 enabled / 6 total rules enforceable.
- Architecture: 5 enabled / 5 total rules enforceable.
- Audit: 2 enabled / 2 total rules enforceable.
- BASIC WORK RULES: 20 enabled / 20 total rules enforceable.
- Basic Readability Rules: 17 enabled / 17 total rules enforceable.
- Basic Work Rules: 8 enabled / 8 total rules enforceable.
- CI / Automated Validation: 7 enabled / 7 total rules enforceable.
- Cache Management: 4 enabled / 4 total rules enforceable.
- Code Review: 2 enabled / 2 total rules enforceable.
- Data Management: 3 enabled / 3 total rules enforceable.
- Determinism: 4 enabled / 4 total rules enforceable.
- Distribution: 1 enabled / 1 total rules enforceable.
- Docs: 14 enabled / 14 total rules enforceable.
- Documentation: 11 enabled / 11 total rules enforceable.
- Error Handling: 32 enabled / 32 total rules enforceable.
- File Structure: 2 enabled / 2 total rules enforceable.
- GSMD — Cursor Enforcement Rules: 21 enabled / 21 total rules enforceable.
- Identifier Authority: 1 enabled / 1 total rules enforceable.
- Lifecycle Management: 2 enabled / 2 total rules enforceable.
- Observability: 43 enabled / 43 total rules enforceable.
- PLATFORM RULES: 6 enabled / 6 total rules enforceable.
- PROBLEM-SOLVING RULES: 8 enabled / 8 total rules enforceable.
- Performance: 4 enabled / 4 total rules enforceable.
- Process Control: 7 enabled / 7 total rules enforceable.
- Project Structure: 4 enabled / 4 total rules enforceable.
- Quality Assurance: 2 enabled / 2 total rules enforceable.
- Readability: 8 enabled / 8 total rules enforceable.
- Reporting: 2 enabled / 2 total rules enforceable.
- SYSTEM DESIGN RULES: 10 enabled / 10 total rules enforceable.
- Schema Requirements: 6 enabled / 6 total rules enforceable.
- Security: 14 enabled / 14 total rules enforceable.
- Simple Code Readability Rules: 28 enabled / 28 total rules enforceable.
- Storage Scripts Enforcement: 24 enabled / 25 total rules enforceable.
- Structural Mapping: 3 enabled / 3 total rules enforceable.
- TYPE SYSTEM RULES: 14 enabled / 14 total rules enforceable.
- Test Data: 2 enabled / 2 total rules enforceable.
- Test Design: 10 enabled / 10 total rules enforceable.
- Testing Governance: 4 enabled / 4 total rules enforceable.
- Testing Infrastructure: 2 enabled / 2 total rules enforceable.
- Testing Philosophy: 8 enabled / 8 total rules enforceable.
- Testing Process: 2 enabled / 2 total rules enforceable.
- UI: 1 enabled / 1 total rules enforceable.
- 🤝 TEAMWORK RULES: 28 enabled / 28 total rules enforceable.

## Critical Guardrails
- No hardcoded secrets or credentials (R-003).
- No assumptions beyond provided information (R-002).
- Keep all configuration in files/settings, never inline constants (R-004).
- Enforce observability, testing, and documentation rules matching rule metadata.

Always cite the specific rule ID that failed and reference the JSON source to keep responses auditable.
