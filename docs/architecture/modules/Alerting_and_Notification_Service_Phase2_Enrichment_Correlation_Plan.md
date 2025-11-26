# Alerting & Notification Service Phase 2 Plan — Enrichment, Deduplication, and Correlation

## Objectives
1. **Enrichment pipeline (FR-2)**  
   - Inject tenant metadata (tier, contacts, quiet hours) from Config & Policy (CPM) and IAM.  
   - Attach component metadata + dependency graph links from Health & Reliability Monitoring (EPC-5).  
   - Pull policy metadata (policy_refs, dedup windows, escalation context) from CPM bundle.  
   - Include latest SLO / health snapshot URL for the component.  
   - Populate `component_metadata`, `slo_snapshot_url`, `policy_refs`, and `automation_hooks` fields automatically.

2. **Configurable deduplication & correlation (FR-3)**  
   - Dedup window derived per alert based on category/severity/policy overrides.  
   - When dedup window expires, new incident is created automatically.  
   - Correlation engine groups alerts into incidents when tenant + plane + time window align and dependency relationships match configured rules.  
   - Persist correlated alert IDs and dependency references on incidents.

## Key Components
| Component | Responsibilities | Data Sources |
| --- | --- | --- |
| `EnrichmentService` | Accept `Alert` model, augment with tenant, component, policy, SLO data. | CPM policy bundle, IAM API (future), EPC-5 metadata service. |
| `DependencyGraphClient` | Fetch dependency edges for component/service. | EPC-5. |
| `CorrelationService` | Evaluate correlation rules, decide whether to attach to existing incident or create new. | Enriched alert, dependency graph, policy bundle. |
| `PolicyClient` (existing) | Already returns dedup + routing info; extend to surface correlation rules and enrichment configs. | CPM policy bundle. |

## Data Contracts
- **Tenant metadata**: `{ "tenant_id": "...", "tier": "...", "contact_groups": [...], "quiet_hours": {...} }`
- **Component metadata**: `{ "component_id": "...", "service_name": "...", "dependencies": ["comp-a", "comp-b"], "slo_snapshot_url": "https://..." }`
- **Correlation rule** (from policy bundle):  
```json
{
  "name": "tenant-plane",
  "conditions": ["tenant_id", "plane"],
  "window_minutes": 10,
  "dependency_match": "shared"
}
```

## Implementation Steps
1. Extend policy bundle schema to include enrichment + correlation config (dependency rules, metadata endpoints).  
2. Build `EnrichmentService` (new file) to:
   - Accept `Alert` (SQLModel entity), call `TenantMetadataClient`, `ComponentMetadataClient`, `PolicyClient`.
   - Update alert fields in-place before `AlertIngestionService.ingest`.
3. Introduce `CorrelationService` invoked inside ingestion:
   - Query recent incidents matching tenant/plane/time window.  
   - Evaluate dependency overlap + policy conditions.  
   - Either attach alert to existing incident (updating `alert_ids`, `correlation_keys`), or create new incident.  
4. Update tests to cover enrichment injection (mock clients) and correlation logic with multiple alerts.  
5. Capture new metrics for enrichment latency and correlation decisions.

## Acceptance Criteria
- Alerts persist enriched metadata without callers supplying it.  
- Policy-configured dedup windows and correlation rules applied per alert.  
- Alerts sharing tenant+plane+dependency within window are grouped under a single incident.  
- Unit tests for enrichment and correlation logic; integration test showing two alerts dedupe/correlate according to policy.  
- Documentation updated (this file + Alerting & Notification Service status sheet).  

