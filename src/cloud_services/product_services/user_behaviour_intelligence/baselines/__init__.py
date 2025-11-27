"""
Baseline computation components for UBI Module (EPC-9).

What: Baseline computation using EMA algorithm, storage, and recomputation
Why: Maintain rolling baselines for anomaly detection per PRD FR-3
Reads/Writes: Baseline computation and storage
Contracts: UBI PRD FR-3, Section 10.3
Risks: Baseline computation errors, warm-up period handling
"""

