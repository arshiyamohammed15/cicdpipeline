# Query Requirements for Receipt Database Design

**Status:** Ready for Database Design  
**Date:** 2025-11-05  
**Version:** 1.0

## Overview

This document defines the concrete query requirements for the receipt storage system. These queries will be used to design the database schema, indexes, and query patterns for both the VS Code Extension (read-only) and backend services (read/write).

---

## 1. VS Code Extension Queries (Read-Only)

### 1.1 Get Latest Receipts for Repository
**Purpose:** Display recent receipts in Extension UI  
**Frequency:** High (on UI load, refresh)  
**Query Pattern:**
```
SELECT * FROM receipts 
WHERE repo_id = ? 
ORDER BY timestamp_utc DESC 
LIMIT 10
```

**Parameters:**
- `repo_id` (string, kebab-case)

**Returns:** Array of DecisionReceipt objects

**Index Required:** `(repo_id, timestamp_utc DESC)`

---

### 1.2 Get Receipt by ID
**Purpose:** Display specific receipt details  
**Frequency:** Medium (user clicks receipt)  
**Query Pattern:**
```
SELECT * FROM receipts 
WHERE receipt_id = ?
```

**Parameters:**
- `receipt_id` (string)

**Returns:** Single DecisionReceipt object or null

**Index Required:** `(receipt_id)` - Primary key or unique index

---

### 1.3 Get Feedback Receipts for Decision Receipt
**Purpose:** Show feedback associated with a decision  
**Frequency:** Medium (user views receipt details)  
**Query Pattern:**
```
SELECT * FROM feedback_receipts 
WHERE decision_receipt_id = ? 
ORDER BY timestamp_utc DESC
```

**Parameters:**
- `decision_receipt_id` (string)

**Returns:** Array of FeedbackReceipt objects

**Index Required:** `(decision_receipt_id, timestamp_utc DESC)`

---

### 1.4 Get Receipts by Date Range
**Purpose:** Filter receipts by time period  
**Frequency:** Low (user filters by date)  
**Query Pattern:**
```
SELECT * FROM receipts 
WHERE repo_id = ? 
  AND timestamp_utc >= ? 
  AND timestamp_utc <= ? 
ORDER BY timestamp_utc DESC
```

**Parameters:**
- `repo_id` (string)
- `start_date` (ISO 8601 string)
- `end_date` (ISO 8601 string)

**Returns:** Array of DecisionReceipt objects

**Index Required:** `(repo_id, timestamp_utc)` - Already covered by 1.1

---

### 1.5 Get Receipts by Decision Status
**Purpose:** Filter receipts by pass/warn/block status  
**Frequency:** Medium (user filters by status)  
**Query Pattern:**
```
-- Option A: If decision.status is stored as JSON
SELECT * FROM receipts 
WHERE repo_id = ? 
  AND JSON_EXTRACT(decision, '$.status') = ? 
ORDER BY timestamp_utc DESC 
LIMIT 50

-- Option B: If decision_status is extracted to separate column
SELECT * FROM receipts 
WHERE repo_id = ? 
  AND decision_status = ? 
ORDER BY timestamp_utc DESC 
LIMIT 50
```

**Parameters:**
- `repo_id` (string)
- `decision_status` ('pass' | 'warn' | 'soft_block' | 'hard_block')

**Returns:** Array of DecisionReceipt objects

**Index Required:** `(repo_id, decision_status, timestamp_utc DESC)`

**Note:** Database schema design will decide whether to:
- Store `decision` as JSON and use JSON queries (Option A)
- Extract `decision.status` to separate `decision_status` column (Option B)
- TypeScript type has nested structure: `decision: { status: '...', rationale: string, badges: string[] }`

---

### 1.6 Get Receipts by Policy Version
**Purpose:** Show receipts for specific policy version  
**Frequency:** Low (user filters by policy)  
**Query Pattern:**
```
SELECT * FROM receipts 
WHERE repo_id = ? 
  AND policy_version_ids LIKE ? 
ORDER BY timestamp_utc DESC
```

**Parameters:**
- `repo_id` (string)
- `policy_version_id` (string, partial match)

**Returns:** Array of DecisionReceipt objects

**Index Required:** `(repo_id, policy_version_ids)` - May require full-text search or array index

**Note:** `policy_version_ids` is an array, so query pattern depends on database type:
- **SQLite:** Use JSON functions or separate junction table
- **PostgreSQL:** Use array operators (`@>` or `&&`)

---

## 2. Backend Service Queries (Read/Write)

### 2.1 Insert Decision Receipt
**Purpose:** Store new decision receipt from Edge Agent  
**Frequency:** High (every task processing)  
**Query Pattern:**
```
INSERT INTO receipts (
  receipt_id, gate_id, policy_version_ids, snapshot_hash,
  timestamp_utc, timestamp_monotonic_ms, inputs, decision,
  evidence_handles, actor, degraded, signature
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```

**Parameters:** All DecisionReceipt fields

**Returns:** Insert result (success/failure)

**Constraints:**
- `receipt_id` must be unique
- `signature` must be present (Rule 224)

---

### 2.2 Insert Feedback Receipt
**Purpose:** Store feedback receipt from Extension  
**Frequency:** Medium (user provides feedback)  
**Query Pattern:**
```
INSERT INTO feedback_receipts (
  feedback_id, decision_receipt_id, pattern_id, choice,
  tags, actor, timestamp_utc, signature
) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
```

**Parameters:** All FeedbackReceipt fields

**Returns:** Insert result (success/failure)

**Constraints:**
- `feedback_id` must be unique
- `decision_receipt_id` must reference existing receipt (foreign key)
- `signature` must be present (Rule 224)

---

### 2.3 Get Receipt Statistics
**Purpose:** Analytics and reporting  
**Frequency:** Low (periodic reports)  
**Query Pattern:**
```
-- Option A: If decision.status is stored as JSON
SELECT 
  COUNT(*) as total_receipts,
  COUNT(CASE WHEN JSON_EXTRACT(decision, '$.status') = 'pass' THEN 1 END) as pass_count,
  COUNT(CASE WHEN JSON_EXTRACT(decision, '$.status') = 'warn' THEN 1 END) as warn_count,
  COUNT(CASE WHEN JSON_EXTRACT(decision, '$.status') = 'soft_block' THEN 1 END) as soft_block_count,
  COUNT(CASE WHEN JSON_EXTRACT(decision, '$.status') = 'hard_block' THEN 1 END) as hard_block_count,
  COUNT(CASE WHEN degraded = 1 THEN 1 END) as degraded_count
FROM receipts
WHERE repo_id = ?
  AND timestamp_utc >= ?
  AND timestamp_utc <= ?

-- Option B: If decision_status is extracted to separate column
SELECT 
  COUNT(*) as total_receipts,
  COUNT(CASE WHEN decision_status = 'pass' THEN 1 END) as pass_count,
  COUNT(CASE WHEN decision_status = 'warn' THEN 1 END) as warn_count,
  COUNT(CASE WHEN decision_status = 'soft_block' THEN 1 END) as soft_block_count,
  COUNT(CASE WHEN decision_status = 'hard_block' THEN 1 END) as hard_block_count,
  COUNT(CASE WHEN degraded = 1 THEN 1 END) as degraded_count
FROM receipts
WHERE repo_id = ?
  AND timestamp_utc >= ?
  AND timestamp_utc <= ?
```

**Parameters:**
- `repo_id` (string)
- `start_date` (ISO 8601)
- `end_date` (ISO 8601)

**Returns:** Statistics object

**Index Required:** `(repo_id, timestamp_utc)` - Already covered

---

### 2.4 Get Feedback Statistics
**Purpose:** Feedback analytics  
**Frequency:** Low (periodic reports)  
**Query Pattern:**
```
SELECT 
  pattern_id,
  choice,
  COUNT(*) as count
FROM feedback_receipts
WHERE decision_receipt_id IN (
  SELECT receipt_id FROM receipts WHERE repo_id = ?
)
  AND timestamp_utc >= ?
  AND timestamp_utc <= ?
GROUP BY pattern_id, choice
```

**Parameters:**
- `repo_id` (string)
- `start_date` (ISO 8601)
- `end_date` (ISO 8601)

**Returns:** Array of statistics objects

**Index Required:** `(decision_receipt_id, timestamp_utc)` - Already covered by 1.3

---

### 2.5 Validate Receipt Signature
**Purpose:** Verify receipt integrity (Rule 224)  
**Frequency:** High (on every read)  
**Query Pattern:**
```
SELECT receipt_id, signature, <all_fields_except_signature>
FROM receipts
WHERE receipt_id = ?
```

**Note:** Signature validation is done in application code, not SQL. This query retrieves the receipt for validation.

**Index Required:** `(receipt_id)` - Already covered by 1.2

---

### 2.6 Get Receipts by Gate ID
**Purpose:** Filter by processing gate (e.g., edge-agent, pre-commit)  
**Frequency:** Low (analytics)  
**Query Pattern:**
```
SELECT * FROM receipts 
WHERE repo_id = ? 
  AND gate_id = ? 
ORDER BY timestamp_utc DESC
```

**Parameters:**
- `repo_id` (string)
- `gate_id` (string)

**Returns:** Array of DecisionReceipt objects

**Index Required:** `(repo_id, gate_id, timestamp_utc DESC)`

---

### 2.7 Get Degraded Receipts
**Purpose:** Monitor system health  
**Frequency:** Low (health checks)  
**Query Pattern:**
```
SELECT * FROM receipts 
WHERE repo_id = ? 
  AND degraded = 1 
  AND timestamp_utc >= ? 
ORDER BY timestamp_utc DESC
LIMIT 100
```

**Parameters:**
- `repo_id` (string)
- `start_date` (ISO 8601, typically last 24 hours)

**Returns:** Array of DecisionReceipt objects

**Index Required:** `(repo_id, degraded, timestamp_utc DESC)`

---

## 3. Query Patterns Summary

### High-Frequency Queries (Require Optimized Indexes)
1. **Get Latest Receipts** (1.1) - `(repo_id, timestamp_utc DESC)`
2. **Get Receipt by ID** (1.2) - `(receipt_id)` - Primary key
3. **Insert Decision Receipt** (2.1) - Primary key on `receipt_id`
4. **Insert Feedback Receipt** (2.2) - Primary key on `feedback_id`, foreign key on `decision_receipt_id`

### Medium-Frequency Queries
1. **Get Feedback Receipts** (1.3) - `(decision_receipt_id, timestamp_utc DESC)`
2. **Get Receipts by Status** (1.5) - `(repo_id, decision_status, timestamp_utc DESC)`
3. **Get Receipts by Gate ID** (2.6) - `(repo_id, gate_id, timestamp_utc DESC)`

### Low-Frequency Queries (Can Use Composite Indexes)
1. **Get Receipts by Date Range** (1.4) - Covered by 1.1 index
2. **Get Receipts by Policy Version** (1.6) - May require full-text or array index
3. **Get Receipt Statistics** (2.3) - Covered by 1.1 index
4. **Get Feedback Statistics** (2.4) - Covered by 1.3 index
5. **Get Degraded Receipts** (2.7) - `(repo_id, degraded, timestamp_utc DESC)`

---

## 4. Database Design Considerations

### 4.1 Index Strategy
- **Primary Indexes:** `receipt_id`, `feedback_id` (unique)
- **Composite Indexes:** 
  - `(repo_id, timestamp_utc DESC)` - Most common query pattern
  - `(repo_id, decision_status, timestamp_utc DESC)` - Status filtering
  - `(repo_id, gate_id, timestamp_utc DESC)` - Gate filtering
  - `(repo_id, degraded, timestamp_utc DESC)` - Health monitoring
  - `(decision_receipt_id, timestamp_utc DESC)` - Feedback lookup

### 4.2 JSON Field Storage
- **SQLite:** Store JSON fields as TEXT, use JSON functions for queries
- **PostgreSQL:** Use JSONB for better query performance
- **Array Fields:** `policy_version_ids`, `tags`, `evidence_handles`, `badges`
  - SQLite: Store as JSON array string
  - PostgreSQL: Use array type or JSONB

### 4.3 Partitioning Strategy
- **Time-based partitioning:** By month (YYYY/MM) - matches file storage structure
- **Repository partitioning:** Separate tables or partitions per repo (if scale requires)

### 4.4 Foreign Key Constraints
- `feedback_receipts.decision_receipt_id` → `receipts.receipt_id`
- Enforce referential integrity (cascade delete optional)

### 4.5 Signature Validation
- Store signature as TEXT
- Validation done in application code (not SQL)
- Index on signature for duplicate detection (optional)

---

## 5. Performance Targets

### Query Latency Targets
- **High-frequency queries (1.1, 1.2, 2.1, 2.2):** < 10ms
- **Medium-frequency queries (1.3, 1.5, 2.6):** < 50ms
- **Low-frequency queries (1.4, 1.6, 2.3, 2.4, 2.7):** < 200ms

### Throughput Targets
- **Insert operations:** 100+ receipts/second
- **Read operations:** 1000+ queries/second

---

## 6. Migration Path

### Phase 1: SQLite (Development/Testing)
- Single-file database
- JSON fields as TEXT
- Basic indexes

### Phase 2: PostgreSQL (Production)
- JSONB for better performance
- Advanced indexing (GIN indexes for JSONB)
- Partitioning for scale

---

## 7. Open Questions

1. **Policy Version Array Query:** Best approach for querying `policy_version_ids` array?
   - Option A: Junction table (normalized)
   - Option B: JSON array with database-specific operators
   - Option C: Full-text search index

2. **Receipt Size Limits:** Maximum size for `inputs` and `evidence_handles` JSON?
   - Current: No limit (stored as JSON)
   - Consider: Compression for large receipts

3. **Retention Policy:** How long to keep receipts in database?
   - File storage: Permanent (JSONL append-only)
   - Database: Configurable retention (e.g., 90 days, 1 year)

---

## 8. Next Steps

1. ✅ **Schema Freeze:** Feedback receipt schema frozen (completed)
2. ✅ **Query Requirements:** This document (completed)
3. ⏳ **Database Schema Design:** Create SQL schema with indexes
4. ⏳ **Migration Scripts:** SQLite → PostgreSQL migration
5. ⏳ **Query Implementation:** Implement queries in storage services
6. ⏳ **Performance Testing:** Validate query performance targets

---

**Document Status:** ✅ Ready for Database Design  
**Last Updated:** 2025-11-05

