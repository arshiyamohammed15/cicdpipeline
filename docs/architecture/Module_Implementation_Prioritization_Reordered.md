# ZeroUI Module Implementation Prioritization (Re-Ordered)

**Version:** 2.1
**Last Updated:** 2025-01-XX
**Status:** Updated per analysis report verification, renumbered by EPC-ID order
**Analysis Report:** See `Module_Implementation_Prioritization_ANALYSIS_REPORT.md`
**Configurable Mapping:** See `MODULE_SECTION_MAPPING.json`

---

## Document Metadata

- **Version:** 2.1
- **Last Updated:** 2025-01-XX
- **Change Log:**
  - v2.1: Renumbered completed modules by EPC-ID order (1.1 EPC-1, 1.2 EPC-3, 1.3 EPC-11, 1.4 EPC-12), added configurable mapping file
  - v2.0: Removed EPC-8 (no implementation evidence found), added M-number mappings, added module ID mapping section, added dependency notes
  - v1.0: Initial re-ordered prioritization

---

## Module ID Mapping

This document uses **EPC-/PM-/FM-/CCP-** prefixes for module identification. The codebase uses **M-numbers** (M01-M20 for functional modules, M21+ for platform capabilities).

**Verified Mappings:**
- **EPC-1** → **M21** (Identity & Access Management)
- **EPC-3** → **M23** (Configuration & Policy Management)
- **EPC-11** → **M33** (Key & Trust Management)
- **EPC-12** → **M34** (Contracts & Schema Registry)

**Note:** Complete mapping document pending. See `docs/architecture/MODULE_ID_MAPPING.md` (to be created).

---

## 1. Completed Modules

These modules are already implemented and form the foundation for all subsequent work.

**Note:** Section numbers are ordered by EPC-ID sequence. For configurable mapping, see `MODULE_SECTION_MAPPING.json`.

### 1.1 EPC-1 — Identity & Access Management

- **ID:** EPC-1
- **Codebase ID:** M21
- **Name:** Identity & Access Management
- **Status:** COMPLETED
- **Implementation Location:** `src/cloud-services/shared-services/identity-access-management/`
- **Verification:** Implementation verified with validation reports

---

### 1.2 EPC-3 — Configuration & Policy Management (+ Gold Standards)

- **ID:** EPC-3
- **Codebase ID:** M23
- **Name:** Configuration & Policy Management (+ Gold Standards)
- **Status:** COMPLETED
- **Implementation Location:** `src/cloud-services/shared-services/configuration-policy-management/`
- **Verification:** Implementation verified with validation reports

---

### 1.3 EPC-11 — Key & Trust Management (KMS & Trust Stores)

- **ID:** EPC-11
- **Codebase ID:** M33
- **Name:** Key & Trust Management (KMS & Trust Stores)
- **Status:** COMPLETED
- **Implementation Location:** `src/cloud-services/shared-services/key-management-service/`
- **Verification:** Implementation verified with validation reports

---

### 1.4 EPC-12 — Contracts & Schema Registry

- **ID:** EPC-12
- **Codebase ID:** M34
- **Name:** Contracts & Schema Registry
- **Status:** COMPLETED
- **Implementation Location:** `src/cloud-services/shared-services/contracts-schema-registry/`
- **Verification:** Implementation verified with validation reports

---

## Dependency Modules (Referenced but Not in Prioritization)

The following modules are referenced as dependencies in implemented modules but are not listed in this prioritization document:

- **M27** — Evidence & Audit Ledger (referenced by M21, M23, M33, M34)
- **M29** — Data & Memory Plane (referenced by M21, M23, M33, M34)
- **M32** — Identity & Trust Plane (referenced by M21, M23, M33, M34)

**Note:** These modules may need to be added to the prioritization sequence or may correspond to existing entries under different IDs. Mapping verification pending.

---

## 2. Pending Modules — Implementation Sequence

This section lists **only PENDING** modules in the agreed implementation order.

**Status Definitions:**
- **PENDING:** Module is in the implementation queue but not yet started or partially implemented
- **COMPLETED:** Module is fully implemented, validated, and verified in the codebase
- **ARCHITECTURAL:** Module is a cross-cutting architectural plane, not a linear implementation item

---

### 2.1 PM-3 — Signal Ingestion & Normalization

- **Sequence Position:** 1
- **ID:** PM-3
- **Name:** Signal Ingestion & Normalization
- **Status:** PENDING

---

### 2.2 PM-7 — Evidence & Receipt Indexing Service

- **Sequence Position:** 2
- **ID:** PM-7
- **Name:** Evidence & Receipt Indexing Service
- **Status:** PENDING

---

### 2.3 PM-2 — Cross-Cutting Concern Services

- **Sequence Position:** 3
- **ID:** PM-2
- **Name:** Cross-Cutting Concern Services
- **Status:** PENDING

---

### 2.4 PM-4 — Detection Engine Core

- **Sequence Position:** 4
- **ID:** PM-4
- **Name:** Detection Engine Core
- **Status:** PENDING

---

### 2.5 FM-12 — ZeroUI Agent

- **Sequence Position:** 5
- **ID:** FM-12
- **Name:** ZeroUI Agent
- **Status:** PENDING

---

### 2.6 PM-6 — LLM Gateway & Safety Enforcement

- **Sequence Position:** 6
- **ID:** PM-6
- **Name:** LLM Gateway & Safety Enforcement
- **Status:** PENDING

---

### 2.7 PM-1 — MMM Engine

- **Sequence Position:** 7
- **ID:** PM-1
- **Name:** MMM Engine
- **Status:** PENDING

---

### 2.8 PM-5 — Integration Adapters

- **Sequence Position:** 8
- **ID:** PM-5
- **Name:** Integration Adapters
- **Status:** PENDING

---

### 2.9 FM-13 — Tenant Admin Portal

- **Sequence Position:** 9
- **ID:** FM-13
- **Name:** Tenant Admin Portal
- **Status:** PENDING

---

### 2.10 EPC-4 — Alerting & Notification Service

- **Sequence Position:** 10
- **ID:** EPC-4
- **Name:** Alerting & Notification Service
- **Status:** PENDING

---

### 2.11 EPC-14 — Trust as a Capability

- **Sequence Position:** 11
- **ID:** EPC-14
- **Name:** Trust as a Capability
- **Status:** PENDING

---

### 2.12 EPC-9 — User Behaviour Intelligence

- **Sequence Position:** 12
- **ID:** EPC-9
- **Name:** User Behaviour Intelligence
- **Status:** PENDING

---

### 2.13 FM-8 — Monitoring & Observability Gaps

- **Sequence Position:** 13
- **ID:** FM-8
- **Name:** Monitoring & Observability Gaps
- **Status:** PENDING

---

### 2.14 FM-10 — QA & Testing Deficiencies

- **Sequence Position:** 14
- **ID:** FM-10
- **Name:** QA & Testing Deficiencies
- **Status:** PENDING

---

### 2.15 FM-1 — Release Failures & Rollbacks

- **Sequence Position:** 15
- **ID:** FM-1
- **Name:** Release Failures & Rollbacks
- **Status:** PENDING

---

### 2.16 FM-9 — Knowledge Integrity & Discovery

- **Sequence Position:** 16
- **ID:** FM-9
- **Name:** Knowledge Integrity & Discovery
- **Status:** PENDING

---

### 2.17 FM-11 — Tech/Domain Onboarding New Team Member

- **Sequence Position:** 17
- **ID:** FM-11
- **Name:** Tech/Domain Onboarding New Team Member
- **Status:** PENDING

---

### 2.18 FM-7 — Root Cause Analysis

- **Sequence Position:** 18
- **ID:** FM-7
- **Name:** Root Cause Analysis
- **Status:** PENDING

---

### 2.19 FM-4 — Merge Conflicts & Delays

- **Sequence Position:** 19
- **ID:** FM-4
- **Name:** Merge Conflicts & Delays
- **Status:** PENDING

---

### 2.20 FM-6 — Feature Development Blind Spots

- **Sequence Position:** 20
- **ID:** FM-6
- **Name:** Feature Development Blind Spots
- **Status:** PENDING

---

### 2.21 FM-3 — Technical Debt Accumulation

- **Sequence Position:** 21
- **ID:** FM-3
- **Name:** Technical Debt Accumulation
- **Status:** PENDING

---

### 2.22 FM-2 — Working Safely with Legacy Systems

- **Sequence Position:** 22
- **ID:** FM-2
- **Name:** Working Safely with Legacy Systems
- **Status:** PENDING

---

### 2.23 FM-5 — Define Requirements

- **Sequence Position:** 23
- **ID:** FM-5
- **Name:** Define Requirements
- **Status:** PENDING

---

### 2.24 FM-14 — ROI Dashboards

- **Sequence Position:** 24
- **ID:** FM-14
- **Name:** ROI Dashboards
- **Status:** PENDING

---

### 2.25 FM-15 — Product Operations Portal

- **Sequence Position:** 25
- **ID:** FM-15
- **Name:** Product Operations Portal
- **Status:** PENDING

---

### 2.26 EPC-13 — Budgeting, Rate-Limiting & Cost Observability

- **Sequence Position:** 26
- **ID:** EPC-13
- **Name:** Budgeting, Rate-Limiting & Cost Observability
- **Status:** PENDING

---

## 3. Cross-Cutting Planes (Architectural)

These are **architectural planes**, not part of the linear implementation queue. They apply across the above modules.

### 3.1 CCP-1 — Identity & Trust Plane

- **ID:** CCP-1
- **Name:** Identity & Trust Plane
- **Status:** ARCHITECTURAL

---

### 3.2 CCP-2 — Policy & Configuration Plane

- **ID:** CCP-2
- **Name:** Policy & Configuration Plane
- **Status:** ARCHITECTURAL

---

### 3.3 CCP-3 — Evidence & Audit Plane

- **ID:** CCP-3
- **Name:** Evidence & Audit Plane
- **Status:** ARCHITECTURAL

---

### 3.4 CCP-4 — Observability & Reliability Plane

- **ID:** CCP-4
- **Name:** Observability & Reliability Plane
- **Status:** ARCHITECTURAL

---

### 3.5 CCP-5 — Security & Supply Chain Plane

- **ID:** CCP-5
- **Name:** Security & Supply Chain Plane
- **Status:** ARCHITECTURAL

---

### 3.6 CCP-6 — Data & Memory Plane

- **ID:** CCP-6
- **Name:** Data & Memory Plane
- **Status:** ARCHITECTURAL

---

### 3.7 CCP-7 — AI Lifecycle & Safety Plane

- **ID:** CCP-7
- **Name:** AI Lifecycle & Safety Plane
- **Status:** ARCHITECTURAL

---

## 4. Analysis & Verification

This document has been analyzed and verified against the codebase. See `Module_Implementation_Prioritization_ANALYSIS_REPORT.md` for detailed findings.

**Key Changes Made:**
- Removed EPC-8 (Deployment & Infrastructure) from COMPLETED section — no implementation evidence found
- Added M-number mappings for verified completed modules
- Added implementation locations for completed modules
- Added dependency modules section (M27, M29, M32)
- Renumbered completed modules by EPC-ID order (1.1 EPC-1, 1.2 EPC-3, 1.3 EPC-11, 1.4 EPC-12)
- Created configurable mapping file (`MODULE_SECTION_MAPPING.json`) to replace hardcoded references

**Verification Status:**
- **Completed Modules:** 4 of 4 verified (100% accuracy after corrections)
- **Pending Modules:** Status verification pending (naming scheme mapping required)
- **Cross-Cutting Planes:** Correctly classified as architectural

---
