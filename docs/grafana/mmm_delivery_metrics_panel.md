## MMM Delivery Metrics Grafana Panel

This document outlines how to expose and visualise the new delivery metrics (`mmm_delivery_attempts_total`, etc.) in Grafana once the Prometheus scrape path (`/v1/mmm/metrics`) is registered.

### 1. Prometheus Scrape Configuration

```yaml
- job_name: 'mmm-engine'
  scrape_interval: 15s
  metrics_path: /v1/mmm/metrics
  static_configs:
    - targets:
        - mmm-engine.prod:8080
      labels:
        service: mmm_engine
        env: production
```

### 2. Grafana Dashboard Panel (JSON)

```json
{
  "title": "MMM Delivery Outcomes",
  "type": "graph",
  "targets": [
    {
      "expr": "sum(rate(mmm_delivery_attempts_total{result=\"success\"}[5m])) by (channel)",
      "legendFormat": "{{channel}} success",
      "interval": "",
      "refId": "A"
    },
    {
      "expr": "sum(rate(mmm_delivery_attempts_total{result=\"failure\"}[5m])) by (channel)",
      "legendFormat": "{{channel}} failure",
      "interval": "",
      "refId": "B"
    }
  ],
  "yaxes": [
    {
      "format": "ops",
      "label": "Attempts/sec",
      "logBase": 1,
      "min": 0
    },
    {
      "format": "short",
      "show": false
    }
  ],
  "legend": {
    "show": true
  }
}
```

### 3. Alert Examples

- **Delivery Failure Rate Spike**  
  Expression: `sum(rate(mmm_delivery_attempts_total{result="failure"}[5m])) / sum(rate(mmm_delivery_attempts_total[5m])) > 0.1`
- **Channel Silence (no deliveries for 10m)**  
  Expression: `sum(rate(mmm_delivery_attempts_total{channel="ide"}[10m])) == 0`

### 4. Operational Notes

- Ensure `EDGE_AGENT_BASE_URL`, `CI_WORKFLOW_BASE_URL`, and `ALERTING_BASE_URL` env vars are set in production so delivery clients are not disabled.
- When Prometheus is unavailable, the fallback metrics helper keeps delivery stats in memory; Grafana panels will show flatlines (0) until scraping resumes.


