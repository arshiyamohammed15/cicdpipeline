# Alert Rules

This document defines alert rules for SLO violations, with throttling and auto-quieting policies.

## Alert Rule Format

Each alert rule defines:
- **Name**: Alert name
- **Condition**: When to trigger
- **Severity**: Critical, Warning, Info
- **Throttle**: Rate limiting
- **Auto-Quiet**: Auto-quieting rules
- **Notification**: Where to send alerts

## Critical Alerts

### Policy Registry Down
- **Condition**: Policy Registry availability < 99.9% over 5 minutes
- **Severity**: Critical
- **Throttle**: Max 1 alert per 15 minutes
- **Auto-Quiet**: None (always alert)
- **Notification**: PagerDuty, Slack #critical, Email on-call

### Audit Ledger Write Failure
- **Condition**: Audit ledger write failures > 0.1% over 1 minute
- **Severity**: Critical
- **Throttle**: Max 1 alert per 5 minutes
- **Auto-Quiet**: None (always alert)
- **Notification**: PagerDuty, Slack #critical, Email on-call

### Receipt Generation Failure
- **Condition**: Receipt generation failures > 1% over 5 minutes
- **Severity**: Critical
- **Throttle**: Max 1 alert per 10 minutes
- **Auto-Quiet**: None (always alert)
- **Notification**: PagerDuty, Slack #critical

### Policy Snapshot Verification Failure
- **Condition**: Policy snapshot verification failures > 1% over 5 minutes
- **Severity**: Critical
- **Throttle**: Max 1 alert per 10 minutes
- **Auto-Quiet**: None (always alert)
- **Notification**: PagerDuty, Slack #critical

## Warning Alerts

### API Response Time Degraded
- **Condition**: API p50 response time > 200ms over 10 minutes
- **Severity**: Warning
- **Throttle**: Max 1 alert per 30 minutes
- **Auto-Quiet**: Auto-quiet if resolved for 15 minutes
- **Notification**: Slack #alerts

### Extension Activation Slow
- **Condition**: Extension activation time > 50ms over 10 minutes
- **Severity**: Warning
- **Throttle**: Max 1 alert per 30 minutes
- **Auto-Quiet**: Auto-quiet if resolved for 15 minutes
- **Notification**: Slack #alerts

### Status Pill Render Slow
- **Condition**: Status pill render time > 50ms over 10 minutes
- **Severity**: Warning
- **Throttle**: Max 1 alert per 30 minutes
- **Auto-Quiet**: Auto-quiet if resolved for 15 minutes
- **Notification**: Slack #alerts

### SLO Error Budget Exhausted
- **Condition**: Error budget < 10% remaining
- **Severity**: Warning
- **Throttle**: Max 1 alert per 1 hour
- **Auto-Quiet**: None (persist until budget restored)
- **Notification**: Slack #slo, Email team

## Info Alerts

### High Request Volume
- **Condition**: Request volume > 2x baseline over 5 minutes
- **Severity**: Info
- **Throttle**: Max 1 alert per 1 hour
- **Auto-Quiet**: Auto-quiet if volume normalizes for 30 minutes
- **Notification**: Slack #metrics

### Key Rotation Scheduled
- **Condition**: Key rotation scheduled in next 24 hours
- **Severity**: Info
- **Throttle**: Max 1 alert per day
- **Auto-Quiet**: None (informational)
- **Notification**: Slack #security

## Throttling Rules

### Throttle Types

1. **Time-Based**: Maximum N alerts per time window
   - Example: Max 1 alert per 15 minutes

2. **Count-Based**: Maximum N alerts per condition occurrence
   - Example: Max 3 alerts per incident

3. **Exponential Backoff**: Increasing delay between alerts
   - Example: 1min, 2min, 4min, 8min, 16min

### Throttle Implementation

```python
# Pseudo-code
if alert_fired_recently(alert_name, throttle_window):
    skip_alert()
else:
    fire_alert()
    record_alert_time(alert_name)
```

## Auto-Quieting Rules

### Auto-Quiet Conditions

1. **Resolution-Based**: Auto-quiet if condition resolves
   - Example: Auto-quiet if resolved for 15 minutes

2. **Time-Based**: Auto-quiet after duration
   - Example: Auto-quiet after 1 hour if no escalation

3. **Manual**: Require manual quiet
   - Example: Critical alerts never auto-quiet

### Auto-Quiet Implementation

```python
# Pseudo-code
if condition_resolved(alert_name, quiet_duration):
    auto_quiet_alert(alert_name)
```

## Notification Channels

### Critical Alerts
- **PagerDuty**: Immediate page to on-call engineer
- **Slack #critical**: Channel notification
- **Email**: Email to on-call team

### Warning Alerts
- **Slack #alerts**: Channel notification
- **Email**: Daily digest (if multiple warnings)

### Info Alerts
- **Slack #metrics**: Channel notification (optional)

## Alert Escalation

### Escalation Path

1. **Level 1**: On-call engineer (immediate)
2. **Level 2**: Team lead (if not acknowledged in 15 minutes)
3. **Level 3**: Engineering manager (if not resolved in 1 hour)
4. **Level 4**: CTO (if critical and not resolved in 4 hours)

### Escalation Rules

- **Critical**: Escalate after 15 minutes if not acknowledged
- **Warning**: Escalate after 1 hour if not resolved
- **Info**: No escalation (informational only)

## Alert Suppression

### Suppression Rules

1. **Maintenance Windows**: Suppress during scheduled maintenance
2. **Known Issues**: Suppress if issue is known and being worked on
3. **False Positives**: Suppress if alert is determined to be false positive

### Suppression Process

1. Create suppression rule with:
   - Alert name
   - Suppression duration
   - Reason
   - Owner

2. Suppression expires automatically
3. Manual suppression requires approval

## Alert Testing

Alerts are tested:
- **Weekly**: Test critical alerts
- **Monthly**: Test all alerts
- **After Changes**: Test when alert rules change

## Alert Metrics

Track:
- **Alert Volume**: Number of alerts per day
- **False Positive Rate**: Percentage of false positives
- **Response Time**: Time to acknowledge/resolve
- **Alert Fatigue**: Frequency of same alert

