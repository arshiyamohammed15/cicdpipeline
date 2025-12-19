# ZeroUI Architecture - Module Categories V 3.0

> **⚠️ SINGLE SOURCE OF TRUTH**: This document is the **ONLY** authoritative source for module categorization and implementation locations. All other documents reference this document.

## Functional Modules (User-Facing)

These are the helpful tools you see and use, like a coach that gives you tips while you're coding or a reminder that helps prevent mistakes before they happen.

### FM-1 - Release Failures & Rollbacks
- **Purpose**: Prevents release failures and automatically rolls back releases when problems are detected.
- **Features**: Real-time monitoring of releases, automated rollback mechanism, detailed risk assessment.
- **Implementation**:
  - VS Code Extension: `src/vscode-extension/modules/m03-release-failures-rollbacks/`
  - Cloud Service: Not implemented (no `main.py` found)

### FM-2 - Working Safely with Legacy Systems
- **Purpose**: Ensures safe integration with legacy systems while avoiding compatibility issues and system disruptions.
- **Features**: Compatibility checks, integration layer for legacy systems, risk mitigation strategies.
- **Implementation**:
  - VS Code Extension: `src/vscode-extension/modules/m06-legacy-systems-safety/`
  - Cloud Service: Not implemented (no `main.py` found)

### FM-3 - Technical Debt Accumulation
- **Purpose**: Tracks and manages the accumulation of technical debt within the system.
- **Features**: Debt detection, impact analysis, automated prioritization of debt reduction tasks.
- **Implementation**:
  - VS Code Extension: `src/vscode-extension/modules/m07-technical-debt-accumulation/`
  - Cloud Service: Not implemented (no `main.py` found)

### FM-4 - Merge Conflicts & Delays
- **Purpose**: Detects and resolves merge conflicts early in the development process to reduce delays.
- **Features**: Real-time conflict detection, automatic conflict resolution, conflict resolution prioritization.
- **Implementation**:
  - VS Code Extension: `src/vscode-extension/modules/m08-merge-conflicts-delays/`
  - Cloud Service: Not implemented (no `main.py` found)

### FM-5 - Strategic Requirements & Storycraft Engine
- **Purpose**: Helps create clear, well-defined user stories and requirements for development sprints.
- **Features**: Automated generation of user stories, story prioritization, collaborative requirements refinement.
- **Implementation**:
  - VS Code Extension: Not implemented (no module folder found)
  - Cloud Service: Not implemented (no `main.py` found)

### FM-6 - Feature Development Blind Spots
- **Purpose**: Identifies missed features or functionality gaps in the development process.
- **Features**: Gap detection, integration of user feedback, quality checks for feature completeness.
- **Implementation**:
  - VS Code Extension: `src/vscode-extension/modules/m11-feature-dev-blind-spots/`
  - Cloud Service: Not implemented (no `main.py` found)

### FM-7 - Root Cause Analysis
- **Purpose**: Analyzes defects and failures to identify their root causes for long-term improvement.
- **Features**: Incident tracking, automated root cause identification, actionable insights for issue resolution.
- **Implementation**:
  - VS Code Extension: Not implemented (no module folder found)
  - Cloud Service: Not implemented (no `main.py` found)

### FM-8 - Monitoring & Observability Gaps
- **Purpose**: Identifies gaps in monitoring coverage and provides full observability across the system.
- **Features**: Real-time monitoring, observability gap detection, alerting and notifications.
- **Implementation**:
  - VS Code Extension: `src/vscode-extension/modules/m13-monitoring-observability-gaps/`
  - Cloud Service: Not implemented (no `main.py` found)

### FM-9 - Knowledge Integrity & Discovery
- **Purpose**: Ensures that the knowledge base is accurate, up-to-date, and easily discoverable.
- **Features**: Data integrity checks, search and discovery tools, continuous knowledge updates.
- **Implementation**:
  - VS Code Extension: `src/vscode-extension/modules/m18-knowledge-integrity-discovery/`
  - Cloud Service: Not implemented (no `main.py` found)

### FM-10 - QA & Testing Deficiencies
- **Purpose**: Identifies gaps in quality assurance and testing processes, ensuring complete test coverage.
- **Features**: Test coverage analysis, automated test generation, integration testing.
- **Implementation**:
  - VS Code Extension: `src/vscode-extension/modules/m20-qa-testing-deficiencies/`
  - Cloud Service: Not implemented (no `main.py` found)

### FM-11 - Tech/Domain Onboarding New Team Member
- **Purpose**: Streamlines the onboarding process for new team members, ensuring quick ramp-up times.
- **Features**: Personalized onboarding experiences, step-by-step guidance, mentorship integration.
- **Implementation**:
  - VS Code Extension: Not implemented (no module folder found)
  - Cloud Service: Not implemented (no `main.py` found)

### FM-12 - ZeroUI Agent
- **Purpose**: Provides an automated assistant to enhance developer productivity by providing feedback and automating repetitive tasks.
- **Features**: Task automation, real-time feedback, integration with IDE and CI/CD.
- **Implementation**:
  - VS Code Extension: Not implemented (no module folder found)
  - Cloud Service: Not implemented (no `main.py` found)

### FM-13 - Tenant Admin Portal
- **Purpose**: Provides administrative control over the ZeroUI instance, allowing management of users, settings, and configurations.
- **Features**: User management, tenant configuration, monitoring and reports.
- **Implementation**:
  - VS Code Extension: `src/vscode-extension/modules/m14-client-admin-dashboard/`
  - Cloud Service: Not implemented (no `main.py` found)

### FM-14 - ROI Dashboards
- **Purpose**: Provides real-time insights into the effectiveness of ZeroUI interventions, measuring productivity gains and risk reductions.
- **Features**: Metrics dashboard, impact reports, custom reporting.
- **Implementation**:
  - VS Code Extension: `src/vscode-extension/modules/m16-roi-dashboard/`
  - Cloud Service: Not implemented (no `main.py` found)

### FM-15 - Product Operations Portal
- **Purpose**: Provides a comprehensive view into product operations, including service health and team performance.
- **Features**: Operational metrics, team dashboard, service analytics.
- **Implementation**:
  - VS Code Extension: `src/vscode-extension/modules/m15-product-success-monitoring/`
  - Cloud Service: Not implemented (no `main.py` found)

## Platform Modules

These are the behind-the-scenes workers that make everything run smoothly, like the engine of a car that powers all the features without you ever seeing it.

### PM-1 - MMM Engine
- **Purpose**: Orchestrates the **Mirror**, **Mentor**, and **Multiplier** feedback loops to enhance decision-making.
- **Features**: Real-time feedback, task automation, code improvement suggestions.
- **Implementation**:
  - VS Code Extension: `src/vscode-extension/modules/m01-mmm-engine/`
  - Cloud Service: `src/cloud_services/product_services/mmm_engine/main.py`

### PM-2 - Cross-Cutting Concern Services
- **Purpose**: Manages core services like **logging**, **monitoring**, **security**, **IAM**, and **error handling**.
- **Features**: Security enforcement, real-time monitoring, centralized logging.
- **Implementation**:
  - VS Code Extension: `src/vscode-extension/modules/m02-cross-cutting-concern-services/`
  - Cloud Service: `src/shared_libs/cccs/` (shared library, not a standalone service)

### PM-3 - Signal Ingestion & Normalization
- **Purpose**: Normalizes and ingests data signals from external tools and systems.
- **Features**: Signal collection, data normalization, real-time processing.
- **Implementation**:
  - VS Code Extension: `src/vscode-extension/modules/m04-signal-ingestion-normalization/`
  - Cloud Service: `src/cloud_services/product_services/signal-ingestion-normalization/main.py`

### PM-4 - Detection Engine Core
- **Purpose**: Detects risks, such as **failed tests** and **merge conflicts**, to ensure smooth development processes.
- **Features**: Real-time risk detection, automated notifications, alerts.
- **Implementation**:
  - VS Code Extension: `src/vscode-extension/modules/m05-detection-engine-core/`
  - Cloud Service: `src/cloud_services/product_services/detection-engine-core/main.py`

### PM-5 - Integration Adapters
- **Purpose**: Ensures seamless communication between ZeroUI and external tools like **Slack**, **GitHub**, **Jira**.
- **Features**: Tool connectivity, event management, data synchronization.
- **Implementation**:
  - VS Code Extension: `src/vscode-extension/modules/m10-integration-adapters/`
  - Cloud Service: `src/cloud_services/client-services/integration-adapters/main.py`

### PM-6 - LLM Gateway & Safety Enforcement
- **Purpose**: Manages the **LLM calls** and enforces safety checks to ensure secure, compliant AI-powered decision-making.
- **Features**: LLM interaction, safety filters, policy enforcement.
- **Implementation**:
  - VS Code Extension: Not implemented (no module folder found)
  - Cloud Service: `src/cloud_services/llm_gateway/main.py`

### PM-7 - Evidence & Receipt Indexing Service
- **Purpose**: Tracks and documents all actions taken by **ZeroUI agents**, **tools**, and **users**.
- **Features**: Receipt generation, audit trails, indexed search.
- **Implementation**:
  - VS Code Extension: Not implemented (no module folder found)
  - Cloud Service: `src/cloud_services/shared-services/evidence-receipt-indexing-service/main.py`

## Embedded Platform Capabilities

These are the built-in superpowers that all modules share, like security guards that protect every part of the system or message carriers that help different features talk to each other.

### EPC-1 - Identity & Access Management
- **Purpose**: Ensures secure authentication and authorization across all **ZeroUI services**.
- **Features**: RBAC, OAuth 2.0, secure authentication.
- **Implementation**:
  - VS Code Extension: `src/vscode-extension/modules/m21-identity-access-management/`
  - Cloud Service: `src/cloud_services/shared-services/identity-access-management/main.py`

### EPC-2 - Data Governance & Privacy
- **Purpose**: Enforces policies that protect sensitive data and ensure compliance with **GDPR** and **CCPA**.
- **Features**: Data classification, redaction, compliance enforcement.
- **Implementation**:
  - VS Code Extension: Not implemented (no module folder found)
  - Cloud Service: `src/cloud_services/shared-services/data-governance-privacy/main.py`

### EPC-3 - Configuration & Policy Management
- **Purpose**: Manages **configuration policies** and ensures compliance across the platform.
- **Features**: Centralized policy management, real-time policy updates, dynamic enforcement.
- **Implementation**:
  - VS Code Extension: `src/vscode-extension/modules/m23-configuration-policy-management/`
  - Cloud Service: `src/cloud_services/shared-services/configuration-policy-management/main.py`

### EPC-4 - Alerting & Notification Service
- **Purpose**: Monitors system health and sends real-time alerts when thresholds are exceeded.
- **Features**: Threshold-based alerts, real-time notifications, integration with observability tools.
- **Implementation**:
  - VS Code Extension: Not implemented (no module folder found)
  - Cloud Service: `src/cloud_services/shared-services/alerting-notification-service/main.py`

### EPC-5 - Health & Reliability Monitoring
- **Purpose**: Continuously monitors the health and performance of **ZeroUI services**.
- **Features**: Service health monitoring, reliability metrics, failure detection.
- **Implementation**:
  - VS Code Extension: Not implemented (no module folder found)
  - Cloud Service: `src/cloud_services/shared-services/health-reliability-monitoring/main.py`

### EPC-6 - API Gateway & Webhooks
- **Purpose**: Routes **API requests** and enables **webhook integrations** with external systems.
- **Features**: Centralized API routing, webhook management, rate-limiting.
- **Implementation**:
  - VS Code Extension: Not implemented (no module folder found)
  - Cloud Service: Not implemented (no `main.py` found)

### EPC-7 - Backup & Disaster Recovery
- **Purpose**: Ensures the recovery of **ZeroUI services** and **data** in case of failure or disaster.
- **Features**: Automated backups, disaster recovery planning, restore capabilities.
- **Implementation**:
  - VS Code Extension: Not implemented (no module folder found)
  - Cloud Service: `src/bdr/service.py` (standalone module, not under cloud_services)

### EPC-8 - Deployment & Infrastructure
- **Purpose**: Manages the deployment pipeline, infrastructure provisioning, and scaling of ZeroUI services.
- **Features**: Infrastructure as Code, automated deployment, scalability.
- **Implementation**:
  - VS Code Extension: Not implemented (no module folder found)
  - Cloud Service: `src/cloud_services/shared-services/deployment-infrastructure/main.py`

### EPC-9 - User Behaviour Intelligence
- **Purpose**: Tracks user actions and provides insights to improve usability and engagement.
- **Features**: User activity tracking, behavioral analytics, personalized experiences.
- **Implementation**:
  - VS Code Extension: Not implemented (no module folder found)
  - Cloud Service: `src/cloud_services/product_services/user_behaviour_intelligence/main.py`

### EPC-10 - Gold Standards
- **Purpose**: Enforces best practices across all modules for **development**, **testing**, and **deployment**.
- **Features**: Standardized best practices, automated compliance, continuous improvement.
- **Implementation**:
  - VS Code Extension: `src/vscode-extension/modules/m17-gold-standards/`
  - Cloud Service: Not implemented (no `main.py` found)

### EPC-11 - Key & Trust Management (KMS & Trust Stores)
- **Purpose**: Manages cryptographic keys and trust certificates across **ZeroUI services**.
- **Features**: Key management, trust stores, security compliance.
- **Implementation**:
  - VS Code Extension: Not implemented (no module folder found)
  - Cloud Service: `src/cloud_services/shared-services/key-management-service/main.py`

### EPC-12 - Contracts & Schema Registry
- **Purpose**: Ensures **data contracts** and **schemas** are standardized and versioned across services.
- **Features**: Schema validation, contract management, version control.
- **Implementation**:
  - VS Code Extension: Not implemented (no module folder found)
  - Cloud Service: `src/cloud_services/shared-services/contracts-schema-registry/main.py`

### EPC-13 - Budgeting, Rate-Limiting & Cost Observability
- **Purpose**: Tracks resource consumption and enforces rate limits to avoid **cost overruns**.
- **Features**: Cost tracking, rate-limiting, budget compliance.
- **Implementation**:
  - VS Code Extension: Not implemented (no module folder found)
  - Cloud Service: `src/cloud_services/shared-services/budgeting-rate-limiting-cost-observability/main.py`

### EPC-14 - Trust as a Capability
- **Purpose**: Establishes **trust** in **ZeroUI** by enforcing policies for data access and tool interactions.
- **Features**: Trust policies, auditability, security compliance.
- **Implementation**:
  - VS Code Extension: Not implemented (no module folder found)
  - Cloud Service: Not implemented (no `main.py` found)

## Cross-Cutting Planes

These are the shared layers that affect everything at once, like the electrical wiring in a house that powers every room or the rules that everyone in a building must follow.

### CCP-1 - Identity & Trust Plane
- **Purpose**: Manages identity and trust across the system.
- **Features**: Authentication, authorization, access control.
- **Implementation**: Cross-cutting concern implemented through EPC-1 (IAM) and shared libraries

### CCP-2 - Policy & Configuration Plane
- **Purpose**: Enforces policies and configurations across all modules.
- **Features**: Centralized policy management, compliance enforcement.
- **Implementation**: Cross-cutting concern implemented through EPC-3 (Configuration & Policy Management) and PM-2 (CCCS)

### CCP-3 - Evidence & Audit Plane
- **Purpose**: Ensures **auditability** and **traceability** of every action taken.
- **Features**: Receipt generation, audit trails, real-time logging.
- **Implementation**: Cross-cutting concern implemented through PM-7 (Evidence & Receipt Indexing Service)

### CCP-4 - Observability & Reliability Plane
- **Purpose**: Monitors the health and performance of the system.
- **Features**: Service monitoring, SLO tracking, real-time alerts.
- **Implementation**: Cross-cutting concern implemented through EPC-4 (Alerting & Notification Service) and EPC-5 (Health & Reliability Monitoring)

### CCP-5 - Security & Supply Chain Plane
- **Purpose**: Ensures **security** and **trusted tool integrations**.
- **Features**: Security policies, supply chain security, vulnerability scanning.
- **Implementation**: Cross-cutting concern implemented through EPC-2 (Data Governance & Privacy), EPC-11 (KMS), and PM-2 (CCCS)

### CCP-6 - Data & Memory Plane
- **Purpose**: Manages data and stateful memory across all services.
- **Features**: Data storage, context management, memory optimization.
- **Implementation**: Cross-cutting concern implemented through shared storage libraries and service-specific databases

### CCP-7 - AI Lifecycle & Safety Plane
- **Purpose**: Ensures safe use of **AI models** throughout their lifecycle.
- **Features**: Model evaluation, safety enforcement, governance.
- **Implementation**: Cross-cutting concern implemented through PM-6 (LLM Gateway & Safety Enforcement)

---

## Implementation Status Summary

### Cloud Services Implementation Status
- **Implemented**: 16 modules have `main.py` files
- **Not Implemented**: 11 modules do not have cloud service implementations

### VS Code Extension Implementation Status
- **Implemented**: 20 modules have extension folders
- **Not Implemented**: 7 modules do not have extension implementations

### Edge Agent Implementation Status
- Edge Agent modules are infrastructure modules (security-enforcer, cache-manager, etc.) located in `src/edge-agent/modules/`
- These are separate from the business logic modules listed above

---

## Notes

1. **VS Code Extension paths**: All extension modules are located under `src/vscode-extension/modules/`
2. **Cloud Service paths**: Cloud services are organized under `src/cloud_services/{category}/` where category is `client-services`, `product-services`, or `shared-services`
3. **Implementation verification**: This document reflects actual file system state. Paths are verified to exist or explicitly marked as "Not implemented"
4. **Single source of truth**: This document is the ONLY authoritative mapping. All other documents should reference this document rather than duplicating mappings.
