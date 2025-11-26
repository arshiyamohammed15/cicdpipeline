/**
 * K6 performance test for LLM Gateway safe flow.
 * 
 * Per NFR-1 and §12.3, validates latency SLOs:
 * - ≤50ms p95 / 10ms p50 for simple chat requests
 * - ≤80ms p95 / 20ms p50 for full safety suite requests
 * 
 * Test Plan Reference: PT-LLM-01
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const simpleChatLatency = new Trend('llm_gateway_simple_chat_latency_ms');
const fullSafetyLatency = new Trend('llm_gateway_full_safety_latency_ms');
const errorRate = new Rate('llm_gateway_errors');

// Test configuration
export const options = {
  stages: [
    { duration: '2m', target: 50 },   // Ramp up to 50 RPS
    { duration: '5m', target: 50 },   // Stay at 50 RPS
    { duration: '2m', target: 100 },  // Ramp up to 100 RPS
    { duration: '5m', target: 100 }, // Stay at 100 RPS
    { duration: '2m', target: 0 },    // Ramp down
  ],
  thresholds: {
    'llm_gateway_simple_chat_latency_ms': ['p(95)<50', 'p(50)<10'],
    'llm_gateway_full_safety_latency_ms': ['p(95)<80', 'p(50)<20'],
    'llm_gateway_errors': ['rate<0.01'], // <1% error rate
    'http_req_duration': ['p(95)<100'],  // Overall HTTP latency
  },
};

const BASE_URL = __ENV.LLM_GATEWAY_URL || 'http://localhost:8006';

// Benign test payloads from golden corpus
const simpleChatPayload = {
  request_id: 'req-perf-simple-001',
  schema_version: 'v1',
  actor: {
    actor_id: 'test-actor-001',
    actor_type: 'service',
    roles: ['developer'],
    capabilities: ['llm.invoke'],
    scopes: ['llm.chat'],
    session_assurance_level: 'high',
  },
  tenant: {
    tenant_id: 'test-tenant-001',
    region: 'us-east-1',
  },
  logical_model_id: 'default_chat',
  operation_type: 'chat',
  sensitivity_level: 'low',
  system_prompt_id: 'sys-default',
  user_prompt: 'Summarise the current sprint burndown risks for leadership.',
  context_segments: [],
  policy_snapshot_id: 'policy-snap-1',
  policy_version_ids: ['policy-v1'],
  budget: {
    max_tokens: 2048,
    timeout_ms: 2000,
    priority: 'normal',
    temperature: 0.2,
  },
  safety_overrides: {
    fail_open_allowed: false,
  },
};

const fullSafetyPayload = {
  request_id: 'req-perf-full-001',
  schema_version: 'v1',
  actor: {
    actor_id: 'test-actor-002',
    actor_type: 'service',
    roles: ['developer'],
    capabilities: ['llm.invoke'],
    scopes: ['llm.chat'],
    session_assurance_level: 'high',
  },
  tenant: {
    tenant_id: 'test-tenant-002',
    region: 'us-east-1',
  },
  logical_model_id: 'default_chat',
  operation_type: 'chat',
  sensitivity_level: 'high',
  system_prompt_id: 'sys-default',
  user_prompt: 'Analyze these logs for security issues: [sample log data with potential PII]',
  context_segments: [
    {
      segment_id: 'ctx-001',
      segment_type: 'logs',
      label: 'security_logs',
      sensitivity: 'confidential',
      content_ref: {
        hash: 'abc123',
        location: 'logs://security/2024/01',
      },
    },
  ],
  policy_snapshot_id: 'policy-snap-1',
  policy_version_ids: ['policy-v1'],
  budget: {
    max_tokens: 2048,
    timeout_ms: 2000,
    priority: 'normal',
    temperature: 0.2,
  },
  safety_overrides: {
    fail_open_allowed: false,
  },
};

export default function () {
  // Test 1: Simple chat request (minimal safety checks)
  const simpleStart = Date.now();
  const simpleResponse = http.post(
    `${BASE_URL}/api/v1/llm/chat`,
    JSON.stringify(simpleChatPayload),
    {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer test-token',
      },
      tags: { test_type: 'simple_chat' },
    }
  );
  const simpleLatency = Date.now() - simpleStart;
  simpleChatLatency.add(simpleLatency);

  const simpleCheck = check(simpleResponse, {
    'simple chat status is 200': (r) => r.status === 200,
    'simple chat decision is ALLOWED': (r) => {
      const body = JSON.parse(r.body);
      return body.decision === 'ALLOWED';
    },
    'simple chat has receipt_id': (r) => {
      const body = JSON.parse(r.body);
      return body.receipt_id && body.receipt_id.startsWith('rcpt-');
    },
  });

  if (!simpleCheck) {
    errorRate.add(1);
  } else {
    errorRate.add(0);
  }

  sleep(0.1); // 100ms between requests

  // Test 2: Full safety suite request (injection + PII + output filters)
  const fullStart = Date.now();
  const fullResponse = http.post(
    `${BASE_URL}/api/v1/llm/chat`,
    JSON.stringify(fullSafetyPayload),
    {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer test-token',
      },
      tags: { test_type: 'full_safety' },
    }
  );
  const fullLatency = Date.now() - fullStart;
  fullSafetyLatency.add(fullLatency);

  const fullCheck = check(fullResponse, {
    'full safety status is 200': (r) => r.status === 200,
    'full safety has policy_snapshot_id': (r) => {
      const body = JSON.parse(r.body);
      return body.policy_snapshot_id && body.policy_snapshot_id.length > 0;
    },
    'full safety has risk_flags array': (r) => {
      const body = JSON.parse(r.body);
      return Array.isArray(body.risk_flags);
    },
  });

  if (!fullCheck) {
    errorRate.add(1);
  } else {
    errorRate.add(0);
  }

  sleep(0.1); // 100ms between requests
}

export function handleSummary(data) {
  return {
    'stdout': JSON.stringify(data, null, 2),
    'llm_gateway_performance_summary.json': JSON.stringify(data, null, 2),
  };
}

