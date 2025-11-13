"""
Identity & Access Management (IAM) Module M21.

What: Authentication and authorization gatekeeper for ZeroUI ecosystem
Why: Provides secure access control with RBAC/ABAC evaluation, JWT token management, and policy enforcement
Reads/Writes: Reads policies, tokens, writes receipts, audit logs
Contracts: IAM API contract (verify, decision, policies endpoints)
Risks: Security vulnerabilities if tokens/policies mishandled, performance degradation under load
"""

__version__ = "1.1.0"
__module_id__ = "M21"

