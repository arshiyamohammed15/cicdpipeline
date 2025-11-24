import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 50,
  duration: '1m',
};

export default function () {
  const payload = JSON.stringify({
    component_id: 'pm-4',
    tenant_id: 'tenant-default',
    plane: 'Tenant',
    environment: 'prod',
    timestamp: new Date().toISOString(),
    telemetry_type: 'metrics',
    metrics: { latency_p95_ms: Math.random() * 300, error_rate: Math.random() * 0.05 },
    labels: { scenario: 'load' },
  });
  const res = http.post('http://localhost:8095/v1/health/telemetry', payload, {
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${__ENV.K6_AUTH_TOKEN || 'valid_epc1_load'}`,
    },
  });
  check(res, {
    'status is 202': (r) => r.status === 202,
  });
  sleep(0.1);
}

