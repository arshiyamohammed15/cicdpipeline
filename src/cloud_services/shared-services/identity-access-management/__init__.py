"""
Identity & Access Management (IAM) Module (EPC-1).

What: Authentication and authorization gatekeeper for ZeroUI ecosystem
Why: Provides secure access control with RBAC/ABAC evaluation, JWT token management, and policy enforcement
Reads/Writes: Reads policies, tokens, writes receipts, audit logs
Contracts: IAM API contract (verify, decision, policies endpoints)
Risks: Security vulnerabilities if tokens/policies mishandled, performance degradation under load

Note: __module_id__ = "M21" is the code identifier (intentional, do not change).
"""
__version__ = "1.1.0"
__module_id__ = "M21"  # Code identifier for EPC-1
