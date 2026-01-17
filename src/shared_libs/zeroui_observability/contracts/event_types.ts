/**
 * Event type registry for ZeroUI Observability Layer (TypeScript).
 *
 * Defines the 12 minimum required event types per PRD Section 4.2.
 */

export enum EventType {
  // Error and failure tracking
  ERROR_CAPTURED = 'error.captured.v1',
  FAILURE_REPLAY_BUNDLE = 'failure.replay.bundle.v1',

  // Prompt and validation
  PROMPT_VALIDATION_RESULT = 'prompt.validation.result.v1',

  // Memory management
  MEMORY_ACCESS = 'memory.access.v1',
  MEMORY_VALIDATION = 'memory.validation.v1',

  // Evaluation and quality
  EVALUATION_RESULT = 'evaluation.result.v1',
  USER_FLAG = 'user.flag.v1',

  // Bias detection
  BIAS_SCAN_RESULT = 'bias.scan.result.v1',

  // Retrieval evaluation
  RETRIEVAL_EVAL = 'retrieval.eval.v1',

  // Performance
  PERF_SAMPLE = 'perf.sample.v1',

  // Privacy and security
  PRIVACY_AUDIT = 'privacy.audit.v1',

  // Alerting and noise control
  ALERT_NOISE_CONTROL = 'alert.noise_control.v1',
}

export function isValidEventType(eventType: string): boolean {
  return Object.values(EventType).includes(eventType as EventType);
}

export function getEventType(eventType: string): EventType | null {
  try {
    return eventType as EventType;
  } catch {
    return null;
  }
}
