# ZeroUI 2.0 Exception Handling Rules (Enhanced)

🎯 **Purpose:** Keep apps stable, users calm, and debugging easy—by turning messy errors into a few clear, friendly outcomes.

## Scope
Applies to APIs, CLIs, services, IDE extensions, and AI components.  
Keep changes small and consistent across the codebase.

---

## Basic Work Rules

**Rule 1: Prevent First**  
Validate inputs early (required, type, range, size). Prevention beats cure.

**Rule 2: Small, Stable Error Codes**  
Adopt ~10–12 canonical codes with severity levels:
- `HIGH`: DEPENDENCY_FAILED, UNEXPECTED_ERROR, TIMEOUT
- `MEDIUM`: RATE_LIMITED, CONFLICT, INVARIANT_VIOLATION  
- `LOW`: VALIDATION_ERROR, NOT_FOUND, PERMISSION_DENIED, CANCELLED

**Rule 3: Wrap & Chain**  
When a low-level error occurs, wrap it into your code with a friendly message and keep the original as the cause. Never throw raw framework/driver errors at the edges.

**Rule 4: Central Handler at Boundaries**  
Have one handler per surface (API endpoint, CLI entry, IDE command) that:
- maps codes → friendly messages
- sets the right status/exit code  
- logs details (with cause chain)

**Rule 5: Friendly to Users, Detailed in Logs**  
Users see short, calm guidance. Logs contain context and the cause chain. Never leak secrets.

**Rule 6: No Silent Catches**  
Never swallow errors. If you catch it, either fix, retry (if safe), or wrap & bubble to the central handler.

**Rule 7: Add Context**  
Always include where/what (operation name, ids, step) when wrapping. This speeds up root-cause analysis.

**Rule 8: Cleanup Always**  
Close files, sockets, timers; release locks. Use "always-run" cleanup paths. Avoid resource leaks.

**Rule 9: Error Recovery Patterns**  
Define clear recovery actions for each error type:
- After `CANCELLED`: Reset operation state
- After `DEPENDENCY_FAILED`: Show fallback content or retry later
- After `VALIDATION_ERROR`: Guide user to correct input
- Document when to show "Try Again" vs. "Contact Support"

**Rule 10: New Developer Onboarding**  
- Provide "First Error Handling Task" template
- Include examples of proper wrapping patterns  
- Document the "why" behind each major rule
- Pair new developers with error handling experts

---

## Timeouts, Retries, Idempotency

**Rule 11: Timeouts Everywhere**  
All I/O (network, file, DB, subprocess) must have a timeout (configurable). No infinite waits.

**Rule 12: Limited Retries with Backoff**  
Retry only idempotent operations. Max 2–3 tries. Use exponential backoff + small jitter.

**Rule 13: Do Not Retry Non-Retriables**  
No retries for validation errors, 401/403, 404, or business rule failures. Surface the issue; guide the user.

**Rule 14: Idempotency**  
Design writes so they are safe to retry (keys/tokens/conflict handling). Document this in your service contract.

---

## Mapping, Messaging, and UX

**Rule 15: HTTP/Exit Mapping**  
Map canonical codes to standard outcomes (e.g., 400/401/403/404/409/422/429/5xx). No "200 with error body".

**Rule 16: Message Catalog**  
Keep a single catalog that maps each code → one friendly, human sentence. Translate here, not in code.

**Rule 17: UI/IDE Behavior**  
Keep UI responsive. Show short, actionable options: Retry / Cancel / Open Logs. No stack traces to users.

---

## Logging, Observability, and Safety

**Rule 18: Structured Logs**  
One JSON object per line. Include: timestamp, level, service, operation, error.code, trace/request ids, duration, attempt, retryable flag, severity, and a cause chain summary.

**Rule 19: Correlation**  
Propagate trace/request ids across calls. Log exactly one request.start and one request.end per request.

**Rule 20: Privacy & Secrets**  
Never log secrets or PII. Redact tokens, passwords, cookies, Authorization headers, and sensitive payloads. Log sizes/hashes, not raw bodies.

---

## Quality, Tests, and Governance

**Rule 21: Test Failure Paths**  
Write tests for:
- Happy path
- Timeouts and 5xx errors  
- 4xx errors (validation/permission)
- Dependency failures
- Cleanup execution verification
- Error cause chain preservation
- Recovery behavior after errors

**Rule 22: Contracts & Docs**  
Document the error envelope, code list, HTTP mapping, and examples. Keep examples up to date and non-PII.

**Rule 23: Consistency Over Cleverness**  
Prefer consistent handling over one-off fixes. If a new case appears, map it to an existing code first.

**Rule 24: Safe Defaults**  
Default timeouts, retry caps, and user messages must be safe and configurable. No hidden magic numbers.

---

## AI-Specific Error Handling

**Rule 25: AI Decision Transparency**  
When AI suggests something, include:
- Confidence level (e.g., "I'm 85% sure this is right")
- Reasoning explanation ("I'm suggesting this because...")
- AI version information ("This was AI version 2.3")

**Rule 26: AI Sandbox Safety**  
AI should only work in a special "playground" (sandbox) away from real computers. It can look at code and make suggestions, but never actually run code on people's machines.

**Rule 27: AI Learning from Mistakes**  
When the AI gets something wrong, it should remember that mistake and get smarter, just like learning from test questions.

**Rule 28: AI Confidence Thresholds**  
- High confidence (>90%): Apply automatically with user notification
- Medium confidence (70-90%): Suggest with explanation
- Low confidence (<70%): Ask for explicit user approval

---

## System Integration & Recovery

**Rule 29: Graceful Degradation**  
When dependencies fail, provide reduced functionality rather than complete failure. Show clear status of what's working vs. limited.

**Rule 30: State Recovery**  
After crashes or failures, systems should recover to known good states. Maintain recovery checkpoints for long-running operations.

**Rule 31: Feature Flag Safety**  
Use feature flags for risky changes with automatic rollback on error detection. Monitor error rates by flag state.

---

## Stop Conditions → Policy Errors (must refuse & escalate)

**ERROR:TOO_MANY_CODES** — New error code added outside the approved catalog.

**ERROR:SILENT_CATCH** — Exception caught without action, wrap, or log.

**ERROR:TIMEOUT_MISSING** — I/O call lacks a timeout.

**ERROR:RETRY_POLICY_VIOLATION** — Retrying a non-idempotent or non-retriable error.

**ERROR:UNMAPPED_HTTP** — Response does not match the standard status mapping.

**ERROR:SECRETS_LEAK** — Sensitive data in messages/logs.

**ERROR:TRACE_MISSING** — request/trace id not propagated to logs.

**ERROR:INCONSISTENT_MESSAGE** — User-facing text not from the catalog.

**ERROR:TESTS_MISSING** — Failure paths not covered by tests.

**ERROR:SEVERITY_MISMATCH** — High severity error treated as low priority.

**ERROR:RECOVERY_MISSING** — No defined recovery path for common errors.

**ERROR:AI_CONFIDENCE_MISSING** — AI decision without confidence level.

**ERROR:STATE_RECOVERY_MISSING** — No recovery mechanism for failed operations.

**ERROR:GRADUAL_DEGRADATION_MISSING** — System fails completely instead of gracefully degrading.

---

## Daily Checklist (Enhanced)

✅ Input validation done (required/type/range/size)  
✅ Timeouts set on all I/O operations  
✅ Risky calls wrapped; no silent catches  
✅ Retries ≤ 3 and idempotent only  
✅ Error wrapped with context; original kept as cause  
✅ Error mapped to canonical code with proper severity  
✅ Central handler shows friendly message; sets proper status  
✅ Recovery action defined for the error type  
✅ AI decisions include confidence and reasoning  
✅ Logs are structured; include trace/request ids and cause chain; no secrets  
✅ HTTP/status mapping matches the standard  
✅ Tests cover success + failures (timeout/5xx/4xx) + cleanup + recovery  
✅ Graceful degradation paths verified  
✅ State recovery mechanisms tested

---

## New Developer Quick Start

**First Error Handling Task:**
1. Pick one endpoint/function
2. Handle `VALIDATION_ERROR` cases  
3. Use the message catalog for user messages
4. Add tests for both success and validation failure
5. Verify cleanup runs in all scenarios
6. Document recovery actions for each error case

**Common Patterns:**
```javascript
// Good: Wrap with context and recovery info
try {
  await database.save(user);
} catch (error) {
  throw new Error('Failed to save user profile', {
    code: 'DEPENDENCY_FAILED',
    severity: 'HIGH',
    cause: error,
    context: { userId: user.id, operation: 'saveProfile' },
    recovery: 'Retry in 5 minutes or contact support if persistent',
    userMessage: 'We\'re having trouble saving your profile right now'
  });
}
```

**Error Severity Response Matrix:**
- **HIGH**: Immediate escalation + user notification + automatic recovery attempts
- **MEDIUM**: Logged for review + user guidance + optional retry
- **LOW**: User guidance only + continued operation

