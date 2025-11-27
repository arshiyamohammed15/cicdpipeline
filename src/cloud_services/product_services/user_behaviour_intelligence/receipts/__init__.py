"""
Receipt generation components for UBI Module (EPC-9).

What: Generate receipts for configuration changes and high-severity signals
Why: Record operations for auditability per PRD FR-13
Reads/Writes: Receipt generation and emission
Contracts: Canonical receipt schema, ERIS PRD Section 8.1
Risks: Receipt schema violations, emission failures
"""

