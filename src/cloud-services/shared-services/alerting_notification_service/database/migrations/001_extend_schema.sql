-- Alerting & Notification Service schema extension migration
-- Applies new columns introduced during Phase 1 implementation.

ALTER TABLE alerts ADD COLUMN schema_version TEXT NOT NULL DEFAULT '1.0.0';
ALTER TABLE alerts ADD COLUMN links TEXT NOT NULL DEFAULT '[]';
ALTER TABLE alerts ADD COLUMN runbook_refs TEXT NOT NULL DEFAULT '[]';
ALTER TABLE alerts ADD COLUMN automation_hooks TEXT NOT NULL DEFAULT '[]';
ALTER TABLE alerts ADD COLUMN component_metadata TEXT NOT NULL DEFAULT '{}';
ALTER TABLE alerts ADD COLUMN slo_snapshot_url TEXT;
ALTER TABLE alerts ADD COLUMN snoozed_until DATETIME;

ALTER TABLE incidents ADD COLUMN schema_version TEXT NOT NULL DEFAULT '1.0.0';
ALTER TABLE incidents ADD COLUMN mitigated_at DATETIME;
ALTER TABLE incidents ADD COLUMN alert_ids TEXT NOT NULL DEFAULT '[]';
ALTER TABLE incidents ADD COLUMN correlation_keys TEXT NOT NULL DEFAULT '[]';
ALTER TABLE incidents ADD COLUMN dependency_refs TEXT NOT NULL DEFAULT '[]';
ALTER TABLE incidents ADD COLUMN policy_refs TEXT NOT NULL DEFAULT '[]';
ALTER TABLE incidents ADD COLUMN plane TEXT;
ALTER TABLE incidents ADD COLUMN component_id TEXT;

ALTER TABLE notifications ADD COLUMN schema_version TEXT NOT NULL DEFAULT '1.0.0';
ALTER TABLE notifications ADD COLUMN next_attempt_at DATETIME;
ALTER TABLE notifications ADD COLUMN failure_reason TEXT;
ALTER TABLE notifications ADD COLUMN channel_context TEXT NOT NULL DEFAULT '{}';
ALTER TABLE notifications ADD COLUMN policy_id TEXT;

ALTER TABLE escalation_policies ADD COLUMN fallback_targets TEXT NOT NULL DEFAULT '[]';
ALTER TABLE escalation_policies ADD COLUMN policy_metadata TEXT NOT NULL DEFAULT '{}';

ALTER TABLE user_notification_preferences ADD COLUMN timezone TEXT NOT NULL DEFAULT 'UTC';
ALTER TABLE user_notification_preferences ADD COLUMN channel_preferences TEXT NOT NULL DEFAULT '{}';
ALTER TABLE user_notification_preferences ADD COLUMN updated_at DATETIME DEFAULT (CURRENT_TIMESTAMP);

