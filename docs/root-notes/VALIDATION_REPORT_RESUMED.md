# ZEROUI 2.0 Constitution Validation Report

**Generated:** 2025-11-20 10:00:16

## Summary

- **Total Files**: 164
- **Total Violations**: 1724
- **Average Compliance**: 55.8%

### Violations by Severity

- **Errors**: 4
- **Warnings**: 704
- **Info**: 1016

### Performance Summary


## File Details

### ❌ models.py

- **Path**: `src\cloud-services\shared-services\contracts-schema-registry\models.py`
- **Compliance**: 37.4%
- **Total Violations**: 41
- **Processing Time**: 0.040s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 36
- **Info**: 5

#### Violations

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 27**: Hardcoded value detected on line 27 - should use settings file
- **Code**: `name: str = Field(..., description="Schema name", min_length=1, max_length=255)`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 27**: Hardcoded value detected on line 27 - should use settings file
- **Code**: `name: str = Field(..., description="Schema name", min_length=1, max_length=255)`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 28**: Hardcoded value detected on line 28 - should use settings file
- **Code**: `namespace: str = Field(..., description="Schema namespace", min_length=1, max_length=255)`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 28**: Hardcoded value detected on line 28 - should use settings file
- **Code**: `namespace: str = Field(..., description="Schema namespace", min_length=1, max_length=255)`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 69**: Hardcoded value detected on line 69 - should use settings file
- **Code**: `name: str = Field(..., description="Contract name", min_length=1, max_length=255)`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 69**: Hardcoded value detected on line 69 - should use settings file
- **Code**: `name: str = Field(..., description="Contract name", min_length=1, max_length=255)`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 72**: Hardcoded value detected on line 72 - should use settings file
- **Code**: `validation_rules: List[Dict[str, Any]] = Field(..., description="Validation rules", min_items=1)`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 72**: Hardcoded value detected on line 72 - should use settings file
- **Code**: `validation_rules: List[Dict[str, Any]] = Field(..., description="Validation rules", min_items=1)`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 74**: Hardcoded value detected on line 74 - should use settings file
- **Code**: `violation_actions: List[str] = Field(..., description="Violation actions", min_items=1)`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 74**: Hardcoded value detected on line 74 - should use settings file
- **Code**: `violation_actions: List[str] = Field(..., description="Violation actions", min_items=1)`
- **Fix**: Move hardcoded values to configuration files

*... and 31 more violations*

---

### ❌ routes.py

- **Path**: `src\cloud-services\shared-services\contracts-schema-registry\routes.py`
- **Compliance**: 37.5%
- **Total Violations**: 24
- **Processing Time**: 0.114s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 21
- **Info**: 3

#### Violations

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 198**: Hardcoded value detected on line 198 - should use settings file
- **Code**: `limit: int = Query(100, ge=1, le=1000),`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 334**: Hardcoded value detected on line 334 - should use settings file
- **Code**: `limit: int = Query(100, ge=1, le=100),`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 362**: Hardcoded value detected on line 362 - should use settings file
- **Code**: `limit: int = Query(100, ge=1, le=100),`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 512**: Hardcoded value detected on line 512 - should use settings file
- **Code**: `limit: int = Query(100, ge=1, le=100),`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 535**: Hardcoded value detected on line 535 - should use settings file
- **Code**: `limit: int = Query(100, ge=1, le=100)`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 645**: Hardcoded value detected on line 645 - should use settings file
- **Code**: `limit=10000,  # Large limit for export`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 664**: Hardcoded value detected on line 664 - should use settings file
- **Code**: `content = json.dumps(export_data, indent=2)`
- **Fix**: Move hardcoded values to configuration files

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

*... and 14 more violations*

---

### ❌ middleware.py

- **Path**: `src\cloud-services\shared-services\contracts-schema-registry\middleware.py`
- **Compliance**: 37.5%
- **Total Violations**: 16
- **Processing Time**: 0.175s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 14
- **Info**: 2

#### Violations

**🟡 Rule 65: Only Use Information You're Given**
- **Line 34**: Magic number detected - use named constants
- **Code**: `= 100`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 65: Only Use Information You're Given**
- **Line 35**: Magic number detected - use named constants
- **Code**: `= 1000`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 65: Only Use Information You're Given**
- **Line 36**: Magic number detected - use named constants
- **Code**: `= 500`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 65: Only Use Information You're Given**
- **Line 37**: Magic number detected - use named constants
- **Code**: `= 5000`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 65: Only Use Information You're Given**
- **Line 39**: Magic number detected - use named constants
- **Code**: `= 500`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 65: Only Use Information You're Given**
- **Line 103**: Magic number detected - use named constants
- **Code**: `= 500`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 65: Only Use Information You're Given**
- **Line 111**: Magic number detected - use named constants
- **Code**: `= 500`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 34**: Hardcoded value detected on line 34 - should use settings file
- **Code**: `RATE_LIMIT_SCHEMA_RPS = 100  # per client`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 35**: Hardcoded value detected on line 35 - should use settings file
- **Code**: `RATE_LIMIT_SCHEMA_TENANT_RPS = 1000  # per tenant`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 36**: Hardcoded value detected on line 36 - should use settings file
- **Code**: `RATE_LIMIT_VALIDATION_RPS = 500  # per client`
- **Fix**: Move hardcoded values to configuration files

*... and 6 more violations*

---

### ❌ models.py

- **Path**: `src\cloud-services\shared-services\identity-access-management\models.py`
- **Compliance**: 38.4%
- **Total Violations**: 33
- **Processing Time**: 0.200s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 28
- **Info**: 5

#### Violations

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 19**: Hardcoded value detected on line 19 - should use settings file
- **Code**: `token: str = Field(..., description="JWT token to verify", min_length=1)`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 19**: Hardcoded value detected on line 19 - should use settings file
- **Code**: `token: str = Field(..., description="JWT token to verify", min_length=1)`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 37**: Hardcoded value detected on line 37 - should use settings file
- **Code**: `min_items=1`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 77**: Hardcoded value detected on line 77 - should use settings file
- **Code**: `incident_id: str = Field(..., description="Incident identifier", min_length=1)`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 77**: Hardcoded value detected on line 77 - should use settings file
- **Code**: `incident_id: str = Field(..., description="Incident identifier", min_length=1)`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 78**: Hardcoded value detected on line 78 - should use settings file
- **Code**: `justification: str = Field(..., description="Justification text (non-PII)", min_length=1)`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 78**: Hardcoded value detected on line 78 - should use settings file
- **Code**: `justification: str = Field(..., description="Justification text (non-PII)", min_length=1)`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 107**: Hardcoded value detected on line 107 - should use settings file
- **Code**: `action: str = Field(..., description="Action to perform", min_length=1)`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 107**: Hardcoded value detected on line 107 - should use settings file
- **Code**: `action: str = Field(..., description="Action to perform", min_length=1)`
- **Fix**: Move hardcoded values to configuration files

*... and 23 more violations*

---

### ❌ models.py

- **Path**: `src\cloud-services\shared-services\key-management-service\models.py`
- **Compliance**: 38.9%
- **Total Violations**: 36
- **Processing Time**: 0.169s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 30
- **Info**: 6

#### Violations

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 28**: Hardcoded value detected on line 28 - should use settings file
- **Code**: `min_items=1`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 41**: Hardcoded value detected on line 41 - should use settings file
- **Code**: `data: str = Field(..., description="Base64-encoded payload to sign", min_length=1)`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 41**: Hardcoded value detected on line 41 - should use settings file
- **Code**: `data: str = Field(..., description="Base64-encoded payload to sign", min_length=1)`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 52**: Hardcoded value detected on line 52 - should use settings file
- **Code**: `data: str = Field(..., description="Base64-encoded payload that was signed", min_length=1)`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 52**: Hardcoded value detected on line 52 - should use settings file
- **Code**: `data: str = Field(..., description="Base64-encoded payload that was signed", min_length=1)`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 53**: Hardcoded value detected on line 53 - should use settings file
- **Code**: `signature: str = Field(..., description="Base64-encoded signature", min_length=1)`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 53**: Hardcoded value detected on line 53 - should use settings file
- **Code**: `signature: str = Field(..., description="Base64-encoded signature", min_length=1)`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 64**: Hardcoded value detected on line 64 - should use settings file
- **Code**: `plaintext: str = Field(..., description="Base64-encoded plaintext", min_length=1)`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 64**: Hardcoded value detected on line 64 - should use settings file
- **Code**: `plaintext: str = Field(..., description="Base64-encoded plaintext", min_length=1)`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 76**: Hardcoded value detected on line 76 - should use settings file
- **Code**: `ciphertext: str = Field(..., description="Base64-encoded ciphertext", min_length=1)`
- **Fix**: Move hardcoded values to configuration files

*... and 26 more violations*

---

### ❌ routes.py

- **Path**: `src\cloud-services\shared-services\budgeting-rate-limiting-cost-observability\routes.py`
- **Compliance**: 39.3%
- **Total Violations**: 61
- **Processing Time**: 0.139s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 50
- **Info**: 11

#### Violations

**🟡 Rule 65: Only Use Information You're Given**
- **Line 214**: Magic number detected - use named constants
- **Code**: `=500`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 65: Only Use Information You're Given**
- **Line 251**: Magic number detected - use named constants
- **Code**: `=400`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 65: Only Use Information You're Given**
- **Line 265**: Magic number detected - use named constants
- **Code**: `=1000`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 65: Only Use Information You're Given**
- **Line 299**: Magic number detected - use named constants
- **Code**: `=500`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 65: Only Use Information You're Given**
- **Line 353**: Magic number detected - use named constants
- **Code**: `=500`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 65: Only Use Information You're Given**
- **Line 410**: Magic number detected - use named constants
- **Code**: `=500`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 65: Only Use Information You're Given**
- **Line 464**: Magic number detected - use named constants
- **Code**: `=500`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 65: Only Use Information You're Given**
- **Line 483**: Magic number detected - use named constants
- **Code**: `=404`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 65: Only Use Information You're Given**
- **Line 494**: Magic number detected - use named constants
- **Code**: `=500`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 65: Only Use Information You're Given**
- **Line 523**: Magic number detected - use named constants
- **Code**: `=404`
- **Fix**: Replace magic numbers with named constants

*... and 51 more violations*

---

### ❌ models.py

- **Path**: `src\cloud-services\shared-services\budgeting-rate-limiting-cost-observability\models.py`
- **Compliance**: 39.7%
- **Total Violations**: 42
- **Processing Time**: 0.187s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 34
- **Info**: 8

#### Violations

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 48**: Hardcoded value detected on line 48 - should use settings file
- **Code**: `pattern="^(BUDGET_EXCEEDED|RATE_LIMIT_VIOLATED|QUOTA_EXHAUSTED|COST_CALCULATION_ERROR|VALIDATION_ERR`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 84**: Hardcoded value detected on line 84 - should use settings file
- **Code**: `pattern="^(budget_threshold_exceeded|rate_limit_violated|cost_anomaly_detected|quota_exhausted)$"`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 107**: Hardcoded value detected on line 107 - should use settings file
- **Code**: `budget_name: str = Field(..., description="Budget name", max_length=255)`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 107**: Hardcoded value detected on line 107 - should use settings file
- **Code**: `budget_name: str = Field(..., description="Budget name", max_length=255)`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 116**: Hardcoded value detected on line 116 - should use settings file
- **Code**: `enforcement_action: str = Field(..., description="Enforcement action", pattern="^(hard_stop|soft_lim`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 140**: Hardcoded value detected on line 140 - should use settings file
- **Code**: `enforcement_action: Optional[str] = Field(default=None, description="Enforcement action", pattern="^`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 160**: Hardcoded value detected on line 160 - should use settings file
- **Code**: `limit_value: int = Field(..., description="Limit value", ge=1)`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 160**: Hardcoded value detected on line 160 - should use settings file
- **Code**: `limit_value: int = Field(..., description="Limit value", ge=1)`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 184**: Hardcoded value detected on line 184 - should use settings file
- **Code**: `limit_value: Optional[int] = Field(default=None, description="Limit value")`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 242**: Hardcoded value detected on line 242 - should use settings file
- **Code**: `description="Report type",`
- **Fix**: Move hardcoded values to configuration files

*... and 32 more violations*

---

### ❌ middleware.py

- **Path**: `src\cloud-services\shared-services\configuration-policy-management\middleware.py`
- **Compliance**: 40.0%
- **Total Violations**: 15
- **Processing Time**: 0.172s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 12
- **Info**: 3

#### Violations

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 34**: Hardcoded value detected on line 34 - should use settings file
- **Code**: `RATE_LIMIT_POLICY_EVAL = 10000  # 10,000 RPS`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 35**: Hardcoded value detected on line 35 - should use settings file
- **Code**: `RATE_LIMIT_CONFIG_RETRIEVAL = 20000  # 20,000 RPS`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 36**: Hardcoded value detected on line 36 - should use settings file
- **Code**: `RATE_LIMIT_COMPLIANCE_CHECK = 5000  # 5,000 RPS`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 37**: Hardcoded value detected on line 37 - should use settings file
- **Code**: `RATE_LIMIT_BURST = 1000  # Burst limit`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 38**: Hardcoded value detected on line 38 - should use settings file
- **Code**: `RATE_LIMIT_BURST_WINDOW = 10  # 10 seconds`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 206**: Hardcoded value detected on line 206 - should use settings file
- **Code**: `rate_limit = 1000  # Default rate limit`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

*... and 5 more violations*

---

### ❌ services.py

- **Path**: `src\cloud-services\shared-services\configuration-policy-management\services.py`
- **Compliance**: 40.4%
- **Total Violations**: 19
- **Processing Time**: 0.151s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 15
- **Info**: 4

#### Violations

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 69**: Hardcoded value detected on line 69 - should use settings file
- **Code**: `CACHE_TTL_POLICY_EVALUATION = 300  # 5 minutes`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 70**: Hardcoded value detected on line 70 - should use settings file
- **Code**: `CACHE_TTL_CONFIGURATION = 60  # 1 minute`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 71**: Hardcoded value detected on line 71 - should use settings file
- **Code**: `CACHE_TTL_COMPLIANCE = 900  # 15 minutes`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 619**: Hardcoded value detected on line 619 - should use settings file
- **Code**: `drift_report["drift_detected"] = True`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 640**: Hardcoded value detected on line 640 - should use settings file
- **Code**: `drift_report["drift_detected"] = True`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 648**: Hardcoded value detected on line 648 - should use settings file
- **Code**: `if drift_report["drift_severity"] != "critical":`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 649**: Hardcoded value detected on line 649 - should use settings file
- **Code**: `drift_report["drift_severity"] = "high"`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 656**: Hardcoded value detected on line 656 - should use settings file
- **Code**: `drift_report["drift_detected"] = True`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 665**: Hardcoded value detected on line 665 - should use settings file
- **Code**: `drift_report["drift_severity"] = "medium"`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 669**: Hardcoded value detected on line 669 - should use settings file
- **Code**: `drift_report["remediation_required"] = True`
- **Fix**: Move hardcoded values to configuration files

*... and 9 more violations*

---

### ❌ main.py

- **Path**: `src\cloud-services\shared-services\budgeting-rate-limiting-cost-observability\main.py`
- **Compliance**: 40.7%
- **Total Violations**: 9
- **Processing Time**: 0.193s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 7
- **Info**: 2

#### Violations

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 25**: Hardcoded value detected on line 25 - should use settings file
- **Code**: `SERVICE_NAME = "budgeting-rate-limiting-cost-observability"`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 60**: Hardcoded value detected on line 60 - should use settings file
- **Code**: `title="ZeroUI Budgeting, Rate-Limiting & Cost Observability",`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 62**: Hardcoded value detected on line 62 - should use settings file
- **Code**: `description="Enterprise-grade resource budgeting, rate-limiting enforcement, and cost transparency f`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 140**: Hardcoded value detected on line 140 - should use settings file
- **Code**: `uvicorn.run(app, host="0.0.0.0", port=8000)`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 140**: Hardcoded value detected on line 140 - should use settings file
- **Code**: `uvicorn.run(app, host="0.0.0.0", port=8000)`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🟡 Rule 65: Only Use Information You're Given**
- **Line 140**: Magic number detected - use named constants
- **Code**: `=8000`
- **Fix**: Replace magic numbers with named constants

---

### ❌ models.py

- **Path**: `src\cloud-services\shared-services\configuration-policy-management\models.py`
- **Compliance**: 41.2%
- **Total Violations**: 17
- **Processing Time**: 0.272s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 13
- **Info**: 4

#### Violations

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 49**: Hardcoded value detected on line 49 - should use settings file
- **Code**: `name: str = Field(..., description="Policy name", min_length=1, max_length=255)`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 49**: Hardcoded value detected on line 49 - should use settings file
- **Code**: `name: str = Field(..., description="Policy name", min_length=1, max_length=255)`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 119**: Hardcoded value detected on line 119 - should use settings file
- **Code**: `name: str = Field(..., description="Configuration name", min_length=1, max_length=255)`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 119**: Hardcoded value detected on line 119 - should use settings file
- **Code**: `name: str = Field(..., description="Configuration name", min_length=1, max_length=255)`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 256**: Hardcoded value detected on line 256 - should use settings file
- **Code**: `reason: str = Field(..., description="Remediation reason", min_length=1)`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 256**: Hardcoded value detected on line 256 - should use settings file
- **Code**: `reason: str = Field(..., description="Remediation reason", min_length=1)`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 286**: Hardcoded value detected on line 286 - should use settings file
- **Code**: `message: str = Field(..., description="Error message", min_length=1)`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 286**: Hardcoded value detected on line 286 - should use settings file
- **Code**: `message: str = Field(..., description="Error message", min_length=1)`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 306**: Hardcoded value detected on line 306 - should use settings file
- **Code**: `url: str = Field(..., description="Evidence URL")`
- **Fix**: Move hardcoded values to configuration files

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

*... and 7 more violations*

---

### ❌ manager.py

- **Path**: `src\cloud-services\shared-services\contracts-schema-registry\cache\manager.py`
- **Compliance**: 41.7%
- **Total Violations**: 16
- **Processing Time**: 0.036s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 12
- **Info**: 4

#### Violations

**🟡 Rule 65: Only Use Information You're Given**
- **Line 22**: Magic number detected - use named constants
- **Code**: `= 3600`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 65: Only Use Information You're Given**
- **Line 23**: Magic number detected - use named constants
- **Code**: `= 300`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 65: Only Use Information You're Given**
- **Line 24**: Magic number detected - use named constants
- **Code**: `= 86400`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 65: Only Use Information You're Given**
- **Line 27**: Magic number detected - use named constants
- **Code**: `= 10000`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 65: Only Use Information You're Given**
- **Line 28**: Magic number detected - use named constants
- **Code**: `= 50000`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 65: Only Use Information You're Given**
- **Line 29**: Magic number detected - use named constants
- **Code**: `= 1000`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 23**: Hardcoded value detected on line 23 - should use settings file
- **Code**: `VALIDATION_CACHE_TTL = 300  # 5 minutes`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 27**: Hardcoded value detected on line 27 - should use settings file
- **Code**: `SCHEMA_CACHE_MAX_ENTRIES = 10000`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 28**: Hardcoded value detected on line 28 - should use settings file
- **Code**: `VALIDATION_CACHE_MAX_ENTRIES = 50000`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 29**: Hardcoded value detected on line 29 - should use settings file
- **Code**: `COMPATIBILITY_CACHE_MAX_ENTRIES = 1000`
- **Fix**: Move hardcoded values to configuration files

*... and 6 more violations*

---

### ❌ services.py

- **Path**: `src\cloud-services\shared-services\contracts-schema-registry\services.py`
- **Compliance**: 41.7%
- **Total Violations**: 20
- **Processing Time**: 0.114s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 15
- **Info**: 5

#### Violations

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 40**: Hardcoded value detected on line 40 - should use settings file
- **Code**: `MAX_SCHEMA_SIZE = 1024 * 1024  # 1MB`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 41**: Hardcoded value detected on line 41 - should use settings file
- **Code**: `MAX_FIELDS_PER_SCHEMA = 1000`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 42**: Hardcoded value detected on line 42 - should use settings file
- **Code**: `MAX_NESTING_DEPTH = 10`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 43**: Hardcoded value detected on line 43 - should use settings file
- **Code**: `MAX_SCHEMA_VERSIONS = 100`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 44**: Hardcoded value detected on line 44 - should use settings file
- **Code**: `MAX_SCHEMAS_PER_TENANT = 10000`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 305**: Hardcoded value detected on line 305 - should use settings file
- **Code**: `limit: int = 100,`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 451**: Hardcoded value detected on line 451 - should use settings file
- **Code**: `return False, [f"Unsupported schema type: {schema_type}"]`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 767**: Hardcoded value detected on line 767 - should use settings file
- **Code**: `limit: int = 100,`
- **Fix**: Move hardcoded values to configuration files

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

*... and 10 more violations*

---

### ❌ models.py

- **Path**: `src\cloud-services\shared-services\budgeting-rate-limiting-cost-observability\database\models.py`
- **Compliance**: 42.1%
- **Total Violations**: 19
- **Processing Time**: 0.135s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 14
- **Info**: 5

#### Violations

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 97**: Hardcoded value detected on line 97 - should use settings file
- **Code**: `CheckConstraint("enforcement_action IN ('hard_stop', 'soft_limit', 'throttle', 'escalate')", name='e`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 131**: Hardcoded value detected on line 131 - should use settings file
- **Code**: `__tablename__ = "rate_limit_policies"`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 138**: Hardcoded value detected on line 138 - should use settings file
- **Code**: `limit_value = Column(Integer, nullable=False)`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 146**: Hardcoded value detected on line 146 - should use settings file
- **Code**: `CheckConstraint("limit_value > 0", name='limit_value_positive'),`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 240**: Hardcoded value detected on line 240 - should use settings file
- **Code**: `max_burst_amount = Column(Numeric(15, 6), nullable=True)`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 247**: Hardcoded value detected on line 247 - should use settings file
- **Code**: `CheckConstraint("used_amount <= allocated_amount + COALESCE(max_burst_amount, 0)", name='quota_used_`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 315**: Hardcoded value detected on line 315 - should use settings file
- **Code**: `__tablename__ = "rate_limit_usage"`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 318**: Hardcoded value detected on line 318 - should use settings file
- **Code**: `policy_id = _uuid_column(ForeignKey('rate_limit_policies.policy_id', ondelete='CASCADE'), nullable=F`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 318**: Hardcoded value detected on line 318 - should use settings file
- **Code**: `policy_id = _uuid_column(ForeignKey('rate_limit_policies.policy_id', ondelete='CASCADE'), nullable=F`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 327**: Hardcoded value detected on line 327 - should use settings file
- **Code**: `UniqueConstraint('policy_id', 'resource_key', 'window_start', name='uq_rate_limit_usage'),`
- **Fix**: Move hardcoded values to configuration files

*... and 9 more violations*

---

### ❌ middleware.py

- **Path**: `src\cloud-services\shared-services\deployment-infrastructure\middleware.py`
- **Compliance**: 42.4%
- **Total Violations**: 11
- **Processing Time**: 0.145s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 8
- **Info**: 3

#### Violations

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

**🟡 Rule 96: Be Extra Careful with Private Data**
- **Line 1**: Private data detected without encryption
- **Code**: `Private data encryption`
- **Fix**: Implement encryption for private data

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 34**: Hardcoded value detected on line 34 - should use settings file
- **Code**: `RATE_LIMIT_RPS = 20`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 35**: Hardcoded value detected on line 35 - should use settings file
- **Code**: `RATE_LIMIT_BURST = 100`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 36**: Hardcoded value detected on line 36 - should use settings file
- **Code**: `RATE_LIMIT_BURST_WINDOW = 10`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

**🟡 Rule 65: Only Use Information You're Given**
- **Line 35**: Magic number detected - use named constants
- **Code**: `= 100`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 65: Only Use Information You're Given**
- **Line 124**: Magic number detected - use named constants
- **Code**: `= 500`
- **Fix**: Replace magic numbers with named constants

*... and 1 more violations*

---

### ❌ middleware.py

- **Path**: `src\cloud-services\shared-services\identity-access-management\middleware.py`
- **Compliance**: 42.4%
- **Total Violations**: 11
- **Processing Time**: 0.103s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 8
- **Info**: 3

#### Violations

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

**🟡 Rule 65: Only Use Information You're Given**
- **Line 35**: Magic number detected - use named constants
- **Code**: `= 200`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 65: Only Use Information You're Given**
- **Line 104**: Magic number detected - use named constants
- **Code**: `= 500`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 65: Only Use Information You're Given**
- **Line 112**: Magic number detected - use named constants
- **Code**: `= 500`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 34**: Hardcoded value detected on line 34 - should use settings file
- **Code**: `RATE_LIMIT_RPS = 50`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 35**: Hardcoded value detected on line 35 - should use settings file
- **Code**: `RATE_LIMIT_BURST = 200`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 36**: Hardcoded value detected on line 36 - should use settings file
- **Code**: `RATE_LIMIT_BURST_WINDOW = 10`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 261**: Hardcoded value detected on line 261 - should use settings file
- **Code**: `if request.method != "PUT" or "/policies" not in str(request.url.path):`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

*... and 1 more violations*

---

### ❌ middleware.py

- **Path**: `src\cloud-services\shared-services\key-management-service\middleware.py`
- **Compliance**: 42.4%
- **Total Violations**: 11
- **Processing Time**: 0.244s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 8
- **Info**: 3

#### Violations

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 34**: Hardcoded value detected on line 34 - should use settings file
- **Code**: `RATE_LIMIT_RPS = 100`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 35**: Hardcoded value detected on line 35 - should use settings file
- **Code**: `RATE_LIMIT_BURST = 500`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 36**: Hardcoded value detected on line 36 - should use settings file
- **Code**: `RATE_LIMIT_BURST_WINDOW = 10`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

**🟡 Rule 65: Only Use Information You're Given**
- **Line 34**: Magic number detected - use named constants
- **Code**: `= 100`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 65: Only Use Information You're Given**
- **Line 35**: Magic number detected - use named constants
- **Code**: `= 500`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 65: Only Use Information You're Given**
- **Line 101**: Magic number detected - use named constants
- **Code**: `= 500`
- **Fix**: Replace magic numbers with named constants

*... and 1 more violations*

---

### ❌ cost_service.py

- **Path**: `src\cloud-services\shared-services\budgeting-rate-limiting-cost-observability\services\cost_service.py`
- **Compliance**: 43.3%
- **Total Violations**: 10
- **Processing Time**: 0.059s

#### Violations by Severity

- **Errors**: 1
- **Warnings**: 5
- **Info**: 4

#### Violations

**🟡 Rule 65: Only Use Information You're Given**
- **Line 130**: Magic number detected - use named constants
- **Code**: `= 100`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 65: Only Use Information You're Given**
- **Line 219**: Magic number detected - use named constants
- **Code**: `=10000`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 65: Only Use Information You're Given**
- **Line 295**: Magic number detected - use named constants
- **Code**: `=10000`
- **Fix**: Replace magic numbers with named constants

**🔴 Rule 66: Protect People's Privacy**
- **Line 237**: Hardcoded credentials/API key detected - security risk
- **Code**: `key = ":"`
- **Fix**: Use environment variables or secure configuration

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 219**: Hardcoded value detected on line 219 - should use settings file
- **Code**: `page_size=10000  # Large page size for reports`
- **Fix**: Move hardcoded values to configuration files

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without version tracking
- **Code**: `AI version tracking`
- **Fix**: Track AI model versions for transparency

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ❌ test_deployment_infrastructure_routes.py

- **Path**: `src\cloud-services\shared-services\deployment-infrastructure\tests\test_deployment_infrastructure_routes.py`
- **Compliance**: 43.3%
- **Total Violations**: 20
- **Processing Time**: 0.349s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 14
- **Info**: 6

#### Violations

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

**🟡 Rule 65: Only Use Information You're Given**
- **Line 28**: Magic number detected - use named constants
- **Code**: `= 200`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 65: Only Use Information You're Given**
- **Line 44**: Magic number detected - use named constants
- **Code**: `= 200`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 65: Only Use Information You're Given**
- **Line 59**: Magic number detected - use named constants
- **Code**: `= 200`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 65: Only Use Information You're Given**
- **Line 72**: Magic number detected - use named constants
- **Code**: `= 422`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 65: Only Use Information You're Given**
- **Line 83**: Magic number detected - use named constants
- **Code**: `= 422`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 65: Only Use Information You're Given**
- **Line 98**: Magic number detected - use named constants
- **Code**: `= 200`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 65: Only Use Information You're Given**
- **Line 116**: Magic number detected - use named constants
- **Code**: `= 200`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 65: Only Use Information You're Given**
- **Line 127**: Magic number detected - use named constants
- **Code**: `= 200`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 65: Only Use Information You're Given**
- **Line 137**: Magic number detected - use named constants
- **Code**: `= 200`
- **Fix**: Replace magic numbers with named constants

*... and 10 more violations*

---

### ❌ routes.py

- **Path**: `src\cloud-services\shared-services\key-management-service\routes.py`
- **Compliance**: 43.6%
- **Total Violations**: 13
- **Processing Time**: 0.166s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 9
- **Info**: 4

#### Violations

**🟡 Rule 65: Only Use Information You're Given**
- **Line 215**: Magic number detected - use named constants
- **Code**: `=2048`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 65: Only Use Information You're Given**
- **Line 386**: Magic number detected - use named constants
- **Code**: `=2048`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 65: Only Use Information You're Given**
- **Line 557**: Magic number detected - use named constants
- **Code**: `=2048`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 65: Only Use Information You're Given**
- **Line 719**: Magic number detected - use named constants
- **Code**: `=256`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 65: Only Use Information You're Given**
- **Line 883**: Magic number detected - use named constants
- **Code**: `=256`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 65: Only Use Information You're Given**
- **Line 1144**: Magic number detected - use named constants
- **Code**: `=2048`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 65: Only Use Information You're Given**
- **Line 1285**: Magic number detected - use named constants
- **Code**: `=2048`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 65: Only Use Information You're Given**
- **Line 1397**: Magic number detected - use named constants
- **Code**: `=2048`
- **Fix**: Replace magic numbers with named constants

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

*... and 3 more violations*

---

### ❌ llm_manager.py

- **Path**: `src\cloud-services\shared-services\ollama-ai-agent\llm_manager.py`
- **Compliance**: 44.4%
- **Total Violations**: 15
- **Processing Time**: 0.223s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 10
- **Info**: 5

#### Violations

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 48**: Hardcoded value detected on line 48 - should use settings file
- **Code**: `with open(config_path, 'r', encoding='utf-8') as f:`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 104**: Hardcoded value detected on line 104 - should use settings file
- **Code**: `def _is_ollama_running(base_url: str = "http://localhost:11434") -> bool:`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 120**: Hardcoded value detected on line 120 - should use settings file
- **Code**: `response = requests.get(tags_endpoint, timeout=2)`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 162**: Hardcoded value detected on line 162 - should use settings file
- **Code**: `timeout=5`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 199**: Hardcoded value detected on line 199 - should use settings file
- **Code**: `timeout=10`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 207**: Hardcoded value detected on line 207 - should use settings file
- **Code**: `timeout=10`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 276**: Hardcoded value detected on line 276 - should use settings file
- **Code**: `max_attempts = 10`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 306**: Hardcoded value detected on line 306 - should use settings file
- **Code**: `self.process.wait(timeout=5)`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without version tracking
- **Code**: `AI version tracking`
- **Fix**: Track AI model versions for transparency

*... and 5 more violations*

---

### ❌ epc13_adapter.py

- **Path**: `src\shared_libs\cccs\adapters\epc13_adapter.py`
- **Compliance**: 45.5%
- **Total Violations**: 11
- **Processing Time**: 0.190s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 7
- **Info**: 4

#### Violations

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 26**: Hardcoded value detected on line 26 - should use settings file
- **Code**: `timeout_seconds: float = 5.0`
- **Fix**: Move hardcoded values to configuration files

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without explanation patterns
- **Code**: `AI explanations`
- **Fix**: Add explanations for AI decisions

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

**🟡 Rule 65: Only Use Information You're Given**
- **Line 90**: Magic number detected - use named constants
- **Code**: `= 429`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 65: Only Use Information You're Given**
- **Line 90**: Magic number detected - use named constants
- **Code**: `= 403`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 65: Only Use Information You're Given**
- **Line 137**: Magic number detected - use named constants
- **Code**: `= 429`
- **Fix**: Replace magic numbers with named constants

*... and 1 more violations*

---

### ❌ services.py

- **Path**: `src\cloud-services\shared-services\identity-access-management\services.py`
- **Compliance**: 45.8%
- **Total Violations**: 8
- **Processing Time**: 0.125s

#### Violations by Severity

- **Errors**: 1
- **Warnings**: 3
- **Info**: 4

#### Violations

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 579**: Hardcoded value detected on line 579 - should use settings file
- **Code**: `requires_dual_approval = "admin" in scope`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 584**: Hardcoded value detected on line 584 - should use settings file
- **Code**: `reason="JIT elevation requires dual approval for admin scope",`
- **Fix**: Move hardcoded values to configuration files

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

**🔴 Rule 66: Protect People's Privacy**
- **Line 58**: Hardcoded credentials/API key detected - security risk
- **Code**: `jti_denylist_key = "iam:jti_denylist"`
- **Fix**: Use environment variables or secure configuration

---

### ❌ runtime.py

- **Path**: `src\shared_libs\cccs\runtime.py`
- **Compliance**: 45.8%
- **Total Violations**: 8
- **Processing Time**: 0.052s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 5
- **Info**: 3

#### Violations

**🟡 Rule 65: Only Use Information You're Given**
- **Line 122**: Magic number detected - use named constants
- **Code**: `= 300`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 122**: Hardcoded value detected on line 122 - should use settings file
- **Code**: `timeout_seconds: float = 300.0,`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 379**: Hardcoded value detected on line 379 - should use settings file
- **Code**: `self._wal_worker.join(timeout=5)`
- **Fix**: Move hardcoded values to configuration files

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without explanation patterns
- **Code**: `AI explanations`
- **Fix**: Add explanations for AI decisions

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ❌ init_db.py

- **Path**: `src\cloud-services\shared-services\data-governance-privacy\database\init_db.py`
- **Compliance**: 46.7%
- **Total Violations**: 10
- **Processing Time**: 0.106s

#### Violations by Severity

- **Errors**: 1
- **Warnings**: 4
- **Info**: 5

#### Violations

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 75**: Hardcoded value detected on line 75 - should use settings file
- **Code**: `return schema_path.read_text(encoding="utf-8")`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 82**: Hardcoded value detected on line 82 - should use settings file
- **Code**: `admin_params["database"] = "postgres"`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 99**: Hardcoded value detected on line 99 - should use settings file
- **Code**: `def initialize_schema(database_url: str, force: bool = False) -> None:`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without version tracking
- **Code**: `AI version tracking`
- **Fix**: Track AI model versions for transparency

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

**🔴 Rule 66: Protect People's Privacy**
- **Line 47**: Hardcoded credentials/API key detected - security risk
- **Code**: `password = "postgres"`
- **Fix**: Use environment variables or secure configuration

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

---

### ❌ service.py

- **Path**: `src\shared_libs\cccs\receipts\service.py`
- **Compliance**: 46.7%
- **Total Violations**: 10
- **Processing Time**: 0.076s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 6
- **Info**: 4

#### Violations

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 32**: Hardcoded value detected on line 32 - should use settings file
- **Code**: `epc11_timeout_seconds: float = 5.0`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 35**: Hardcoded value detected on line 35 - should use settings file
- **Code**: `pm7_timeout_seconds: float = 5.0`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 98**: Hardcoded value detected on line 98 - should use settings file
- **Code**: `config.storage_path.parent.mkdir(parents=True, exist_ok=True)`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 196**: Hardcoded value detected on line 196 - should use settings file
- **Code**: `with self._config.storage_path.open("a", encoding="utf-8") as handle:`
- **Fix**: Move hardcoded values to configuration files

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without explanation patterns
- **Code**: `AI explanations`
- **Fix**: Add explanations for AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ❌ init_db.py

- **Path**: `src\cloud-services\shared-services\configuration-policy-management\database\init_db.py`
- **Compliance**: 48.1%
- **Total Violations**: 9
- **Processing Time**: 0.139s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 5
- **Info**: 4

#### Violations

**🟡 Rule 65: Only Use Information You're Given**
- **Line 62**: Magic number detected - use named constants
- **Code**: `= 5432`
- **Fix**: Replace magic numbers with named constants

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 62**: Hardcoded value detected on line 62 - should use settings file
- **Code**: `port = 5432`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 129**: Hardcoded value detected on line 129 - should use settings file
- **Code**: `def initialize_schema(database_url: str, force: bool = False) -> None:`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 208**: Hardcoded value detected on line 208 - should use settings file
- **Code**: `help='PostgreSQL connection URL (default: from DATABASE_URL env var)'`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without version tracking
- **Code**: `AI version tracking`
- **Fix**: Track AI model versions for transparency

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

---

### ❌ init_db.py

- **Path**: `src\cloud-services\shared-services\contracts-schema-registry\database\init_db.py`
- **Compliance**: 48.1%
- **Total Violations**: 9
- **Processing Time**: 0.100s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 5
- **Info**: 4

#### Violations

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 62**: Hardcoded value detected on line 62 - should use settings file
- **Code**: `port = 5432`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 129**: Hardcoded value detected on line 129 - should use settings file
- **Code**: `def initialize_schema(database_url: str, force: bool = False) -> None:`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 209**: Hardcoded value detected on line 209 - should use settings file
- **Code**: `help='PostgreSQL connection URL (default: from DATABASE_URL env var)'`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without version tracking
- **Code**: `AI version tracking`
- **Fix**: Track AI model versions for transparency

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

**🟡 Rule 65: Only Use Information You're Given**
- **Line 62**: Magic number detected - use named constants
- **Code**: `= 5432`
- **Fix**: Replace magic numbers with named constants

---

### ❌ json_schema_validator.py

- **Path**: `src\cloud-services\shared-services\contracts-schema-registry\validators\json_schema_validator.py`
- **Compliance**: 48.5%
- **Total Violations**: 11
- **Processing Time**: 0.250s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 6
- **Info**: 5

#### Violations

**🟡 Rule 65: Only Use Information You're Given**
- **Line 20**: Magic number detected - use named constants
- **Code**: `= 1024`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 65: Only Use Information You're Given**
- **Line 21**: Magic number detected - use named constants
- **Code**: `= 1000`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 20**: Hardcoded value detected on line 20 - should use settings file
- **Code**: `MAX_SCHEMA_SIZE = 1024 * 1024  # 1MB`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 21**: Hardcoded value detected on line 21 - should use settings file
- **Code**: `MAX_FIELDS_PER_SCHEMA = 1000`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 22**: Hardcoded value detected on line 22 - should use settings file
- **Code**: `MAX_NESTING_DEPTH = 10`
- **Fix**: Move hardcoded values to configuration files

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

*... and 1 more violations*

---

### ❌ test_identity_access_management_routes.py

- **Path**: `src\cloud-services\shared-services\identity-access-management\tests\test_identity_access_management_routes.py`
- **Compliance**: 48.7%
- **Total Violations**: 13
- **Processing Time**: 0.248s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 7
- **Info**: 6

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without explanation patterns
- **Code**: `AI explanations`
- **Fix**: Add explanations for AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

**🟡 Rule 65: Only Use Information You're Given**
- **Line 21**: Magic number detected - use named constants
- **Code**: `= 200`
- **Fix**: Replace magic numbers with named constants

*... and 3 more violations*

---

### ❌ models.py

- **Path**: `src\cloud-services\shared-services\ollama-ai-agent\models.py`
- **Compliance**: 48.9%
- **Total Violations**: 15
- **Processing Time**: 0.112s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 8
- **Info**: 7

#### Violations

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 19**: Hardcoded value detected on line 19 - should use settings file
- **Code**: `prompt: str = Field(..., description="The prompt to send to the LLM", min_length=1)`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 19**: Hardcoded value detected on line 19 - should use settings file
- **Code**: `prompt: str = Field(..., description="The prompt to send to the LLM", min_length=1)`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 62**: Hardcoded value detected on line 62 - should use settings file
- **Code**: `code: str = Field(..., description="Error code", min_length=1)`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 62**: Hardcoded value detected on line 62 - should use settings file
- **Code**: `code: str = Field(..., description="Error code", min_length=1)`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 63**: Hardcoded value detected on line 63 - should use settings file
- **Code**: `message: str = Field(..., description="Error message", min_length=1)`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 63**: Hardcoded value detected on line 63 - should use settings file
- **Code**: `message: str = Field(..., description="Error message", min_length=1)`
- **Fix**: Move hardcoded values to configuration files

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

*... and 5 more violations*

---

### ❌ middleware.py

- **Path**: `src\cloud-services\shared-services\budgeting-rate-limiting-cost-observability\middleware.py`
- **Compliance**: 50.0%
- **Total Violations**: 16
- **Processing Time**: 0.080s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 8
- **Info**: 8

#### Violations

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 84**: Hardcoded value detected on line 84 - should use settings file
- **Code**: `limit = 1000`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 103**: Hardcoded value detected on line 103 - should use settings file
- **Code**: `self.rate_limits[key]["count"] += 1`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 126**: Hardcoded value detected on line 126 - should use settings file
- **Code**: `if request.url.path == "/budget/v1/health":`
- **Fix**: Move hardcoded values to configuration files

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without version tracking
- **Code**: `AI version tracking`
- **Fix**: Track AI model versions for transparency

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

*... and 6 more violations*

---

### ❌ test_rate_limit_service.py

- **Path**: `src\cloud-services\shared-services\budgeting-rate-limiting-cost-observability\tests\test_rate_limit_service.py`
- **Compliance**: 50.0%
- **Total Violations**: 16
- **Processing Time**: 0.275s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 8
- **Info**: 8

#### Violations

**🟡 Rule 65: Only Use Information You're Given**
- **Line 109**: Magic number detected - use named constants
- **Code**: `= 120`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 39**: Hardcoded value detected on line 39 - should use settings file
- **Code**: `def create_policy(service, tenant_id, algorithm, overrides=None, burst_capacity=None, limit_value=10`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 62**: Hardcoded value detected on line 62 - should use settings file
- **Code**: `policy = create_policy(rate_limit_service, tenant_id, "leaky_bucket", limit_value=5, window_seconds=`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 90**: Hardcoded value detected on line 90 - should use settings file
- **Code**: `policy = create_policy(rate_limit_service, tenant_id, "sliding_window_log", limit_value=3, window_se`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 132**: Hardcoded value detected on line 132 - should use settings file
- **Code**: `limit_value=10,`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 159**: Hardcoded value detected on line 159 - should use settings file
- **Code**: `assert result["limit_value"] == 5`
- **Fix**: Move hardcoded values to configuration files

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

*... and 6 more violations*

---

### ❌ custom_validator.py

- **Path**: `src\cloud-services\shared-services\contracts-schema-registry\validators\custom_validator.py`
- **Compliance**: 50.0%
- **Total Violations**: 12
- **Processing Time**: 0.144s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 6
- **Info**: 6

#### Violations

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 20**: Hardcoded value detected on line 20 - should use settings file
- **Code**: `MINI_RACER_AVAILABLE = True`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 22**: Hardcoded value detected on line 22 - should use settings file
- **Code**: `MINI_RACER_AVAILABLE = False`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 26**: Hardcoded value detected on line 26 - should use settings file
- **Code**: `MAX_EXECUTION_TIME_MS = 100`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 27**: Hardcoded value detected on line 27 - should use settings file
- **Code**: `MAX_MEMORY_MB = 64`
- **Fix**: Move hardcoded values to configuration files

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without version tracking
- **Code**: `AI version tracking`
- **Fix**: Track AI model versions for transparency

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

*... and 2 more violations*

---

### ❌ services.py

- **Path**: `src\cloud-services\shared-services\key-management-service\services.py`
- **Compliance**: 50.0%
- **Total Violations**: 8
- **Processing Time**: 0.084s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 4
- **Info**: 4

#### Violations

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 34**: Hardcoded value detected on line 34 - should use settings file
- **Code**: `DEFAULT_MAX_USAGE_PER_DAY = 1000`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 604**: Hardcoded value detected on line 604 - should use settings file
- **Code**: `return False, f"Daily usage limit exceeded: {usage_count}/{key_metadata.access_policy.max_usage_per_`
- **Fix**: Move hardcoded values to configuration files

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

**🟡 Rule 65: Only Use Information You're Given**
- **Line 34**: Magic number detected - use named constants
- **Code**: `= 1000`
- **Fix**: Replace magic numbers with named constants

---

### ❌ services.py

- **Path**: `src\cloud-services\shared-services\ollama-ai-agent\services.py`
- **Compliance**: 50.0%
- **Total Violations**: 8
- **Processing Time**: 0.184s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 4
- **Info**: 4

#### Violations

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 44**: Hardcoded value detected on line 44 - should use settings file
- **Code**: `with open(config_path, 'r', encoding='utf-8') as f:`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 105**: Hardcoded value detected on line 105 - should use settings file
- **Code**: `response = requests.get(tags_endpoint, timeout=5)`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without version tracking
- **Code**: `AI version tracking`
- **Fix**: Track AI model versions for transparency

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

**🟡 Rule 65: Only Use Information You're Given**
- **Line 106**: Magic number detected - use named constants
- **Code**: `= 200`
- **Fix**: Replace magic numbers with named constants

---

### ❌ cloud_services_integration.py

- **Path**: `src\shared_libs\cccs\integration\cloud_services_integration.py`
- **Compliance**: 50.0%
- **Total Violations**: 10
- **Processing Time**: 0.025s

#### Violations by Severity

- **Errors**: 1
- **Warnings**: 3
- **Info**: 6

#### Violations

**🔴 Rule 66: Protect People's Privacy**
- **Line 140**: Hardcoded credentials/API key detected - security risk
- **Code**: `config_key="config-key"`
- **Fix**: Use environment variables or secure configuration

**🟡 Rule 65: Only Use Information You're Given**
- **Line 94**: Magic number detected - use named constants
- **Code**: `=500`
- **Fix**: Replace magic numbers with named constants

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without explanation patterns
- **Code**: `AI explanations`
- **Fix**: Add explanations for AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without version tracking
- **Code**: `AI version tracking`
- **Fix**: Track AI model versions for transparency

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ❌ service.py

- **Path**: `src\shared_libs\cccs\identity\service.py`
- **Compliance**: 50.0%
- **Total Violations**: 8
- **Processing Time**: 0.043s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 4
- **Info**: 4

#### Violations

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 21**: Hardcoded value detected on line 21 - should use settings file
- **Code**: `epc1_timeout_seconds: float = 5.0`
- **Fix**: Move hardcoded values to configuration files

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without explanation patterns
- **Code**: `AI explanations`
- **Fix**: Add explanations for AI decisions

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ❌ pm7_adapter.py

- **Path**: `src\shared_libs\cccs\adapters\pm7_adapter.py`
- **Compliance**: 50.0%
- **Total Violations**: 8
- **Processing Time**: 0.128s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 4
- **Info**: 4

#### Violations

**🟡 Rule 65: Only Use Information You're Given**
- **Line 107**: Magic number detected - use named constants
- **Code**: `= 200`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 23**: Hardcoded value detected on line 23 - should use settings file
- **Code**: `timeout_seconds: float = 5.0`
- **Fix**: Move hardcoded values to configuration files

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without explanation patterns
- **Code**: `AI explanations`
- **Fix**: Add explanations for AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ❌ epc3_adapter.py

- **Path**: `src\shared_libs\cccs\adapters\epc3_adapter.py`
- **Compliance**: 50.0%
- **Total Violations**: 8
- **Processing Time**: 0.159s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 4
- **Info**: 4

#### Violations

**🟡 Rule 65: Only Use Information You're Given**
- **Line 232**: Magic number detected - use named constants
- **Code**: `= 200`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 28**: Hardcoded value detected on line 28 - should use settings file
- **Code**: `timeout_seconds: float = 5.0`
- **Fix**: Move hardcoded values to configuration files

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without explanation patterns
- **Code**: `AI explanations`
- **Fix**: Add explanations for AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ❌ deploy.py

- **Path**: `src\cloud-services\shared-services\deployment-infrastructure\scripts\deploy.py`
- **Compliance**: 51.5%
- **Total Violations**: 11
- **Processing Time**: 0.223s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 5
- **Info**: 6

#### Violations

**🟡 Rule 65: Only Use Information You're Given**
- **Line 78**: Magic number detected - use named constants
- **Code**: `=300`
- **Fix**: Replace magic numbers with named constants

**🔵 Rule 65: Only Use Information You're Given**
- **Line 84**: Assumption detected in code or comments
- **Code**: `Estimate`
- **Fix**: Use only information explicitly provided

**🔵 Rule 65: Only Use Information You're Given**
- **Line 84**: Assumption detected in code or comments
- **Code**: `estimate`
- **Fix**: Use only information explicitly provided

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 78**: Hardcoded value detected on line 78 - should use settings file
- **Code**: `timeout=300.0  # 5 minute timeout for deployment`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 120**: Hardcoded value detected on line 120 - should use settings file
- **Code**: `help="Path to deployment configuration file (optional)"`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 124**: Hardcoded value detected on line 124 - should use settings file
- **Code**: `help="Deployment API URL (optional, defaults to http://localhost:8000)"`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without version tracking
- **Code**: `AI version tracking`
- **Fix**: Track AI model versions for transparency

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

*... and 1 more violations*

---

### ❌ wal.py

- **Path**: `src\shared_libs\cccs\receipts\wal.py`
- **Compliance**: 51.5%
- **Total Violations**: 11
- **Processing Time**: 0.039s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 5
- **Info**: 6

#### Violations

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 43**: Hardcoded value detected on line 43 - should use settings file
- **Code**: `self._path.parent.mkdir(parents=True, exist_ok=True)`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 50**: Hardcoded value detected on line 50 - should use settings file
- **Code**: `with self._path.open("r", encoding="utf-8") as handle:`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 73**: Hardcoded value detected on line 73 - should use settings file
- **Code**: `with temp_path.open("w", encoding="utf-8") as handle:`
- **Fix**: Move hardcoded values to configuration files

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without explanation patterns
- **Code**: `AI explanations`
- **Fix**: Add explanations for AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without version tracking
- **Code**: `AI version tracking`
- **Fix**: Track AI model versions for transparency

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

*... and 1 more violations*

---

### ❌ rate_limit_service.py

- **Path**: `src\cloud-services\shared-services\budgeting-rate-limiting-cost-observability\services\rate_limit_service.py`
- **Compliance**: 51.9%
- **Total Violations**: 9
- **Processing Time**: 0.066s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 4
- **Info**: 5

#### Violations

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 339**: Hardcoded value detected on line 339 - should use settings file
- **Code**: `return False, 0, window_end, effective_limit`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 401**: Hardcoded value detected on line 401 - should use settings file
- **Code**: `return False, 0, window_end, adjusted_limit`
- **Fix**: Move hardcoded values to configuration files

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without version tracking
- **Code**: `AI version tracking`
- **Fix**: Track AI model versions for transparency

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

**🟡 Rule 65: Only Use Information You're Given**
- **Line 537**: Magic number detected - use named constants
- **Code**: `= 100`
- **Fix**: Replace magic numbers with named constants

---

### ❌ epc1_adapter.py

- **Path**: `src\shared_libs\cccs\adapters\epc1_adapter.py`
- **Compliance**: 51.9%
- **Total Violations**: 9
- **Processing Time**: 0.058s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 4
- **Info**: 5

#### Violations

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 26**: Hardcoded value detected on line 26 - should use settings file
- **Code**: `timeout_seconds: float = 5.0`
- **Fix**: Move hardcoded values to configuration files

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without explanation patterns
- **Code**: `AI explanations`
- **Fix**: Add explanations for AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

**🟡 Rule 65: Only Use Information You're Given**
- **Line 173**: Magic number detected - use named constants
- **Code**: `= 200`
- **Fix**: Replace magic numbers with named constants

---

### ❌ epc11_adapter.py

- **Path**: `src\shared_libs\cccs\adapters\epc11_adapter.py`
- **Compliance**: 51.9%
- **Total Violations**: 9
- **Processing Time**: 0.140s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 4
- **Info**: 5

#### Violations

**🟡 Rule 65: Only Use Information You're Given**
- **Line 115**: Magic number detected - use named constants
- **Code**: `= 200`
- **Fix**: Replace magic numbers with named constants

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 23**: Hardcoded value detected on line 23 - should use settings file
- **Code**: `timeout_seconds: float = 5.0`
- **Fix**: Move hardcoded values to configuration files

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without explanation patterns
- **Code**: `AI explanations`
- **Fix**: Add explanations for AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ❌ service.py

- **Path**: `src\shared_libs\cccs\ratelimit\service.py`
- **Compliance**: 51.9%
- **Total Violations**: 9
- **Processing Time**: 0.086s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 4
- **Info**: 5

#### Violations

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 21**: Hardcoded value detected on line 21 - should use settings file
- **Code**: `epc13_timeout_seconds: float = 5.0`
- **Fix**: Move hardcoded values to configuration files

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without explanation patterns
- **Code**: `AI explanations`
- **Fix**: Add explanations for AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ❌ aggregator.py

- **Path**: `src\cloud-services\shared-services\contracts-schema-registry\analytics\aggregator.py`
- **Compliance**: 52.4%
- **Total Violations**: 14
- **Processing Time**: 0.084s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 6
- **Info**: 8

#### Violations

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 23**: Hardcoded value detected on line 23 - should use settings file
- **Code**: `RETENTION_HOURLY_DAYS = 7`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 64**: Hardcoded value detected on line 64 - should use settings file
- **Code**: `period="hourly",`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 130**: Hardcoded value detected on line 130 - should use settings file
- **Code**: `SchemaAnalytics.period == "hourly",`
- **Fix**: Move hardcoded values to configuration files

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without version tracking
- **Code**: `AI version tracking`
- **Fix**: Track AI model versions for transparency

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

*... and 4 more violations*

---

### ❌ verify_environment_parity.py

- **Path**: `src\cloud-services\shared-services\deployment-infrastructure\scripts\verify_environment_parity.py`
- **Compliance**: 52.4%
- **Total Violations**: 7
- **Processing Time**: 0.029s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 3
- **Info**: 4

#### Violations

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 61**: Hardcoded value detected on line 61 - should use settings file
- **Code**: `timeout=60.0  # 1 minute timeout for parity check`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 117**: Hardcoded value detected on line 117 - should use settings file
- **Code**: `help="Deployment API URL (optional, defaults to http://localhost:8000)"`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without version tracking
- **Code**: `AI version tracking`
- **Fix**: Track AI model versions for transparency

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ❌ middleware.py

- **Path**: `src\cloud-services\shared-services\ollama-ai-agent\middleware.py`
- **Compliance**: 52.4%
- **Total Violations**: 7
- **Processing Time**: 0.136s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 3
- **Info**: 4

#### Violations

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

**🟡 Rule 65: Only Use Information You're Given**
- **Line 98**: Magic number detected - use named constants
- **Code**: `= 500`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 65: Only Use Information You're Given**
- **Line 106**: Magic number detected - use named constants
- **Code**: `= 500`
- **Fix**: Replace magic numbers with named constants

---

### ❌ test_event_subscription_service.py

- **Path**: `src\cloud-services\shared-services\budgeting-rate-limiting-cost-observability\tests\test_event_subscription_service.py`
- **Compliance**: 52.8%
- **Total Violations**: 12
- **Processing Time**: 0.152s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 5
- **Info**: 7

#### Violations

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 30**: Hardcoded value detected on line 30 - should use settings file
- **Code**: `webhook_url="https://example.com/webhook",`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 65**: Hardcoded value detected on line 65 - should use settings file
- **Code**: `webhook_url="https://example.com/webhook",`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 79**: Hardcoded value detected on line 79 - should use settings file
- **Code**: `webhook_url="https://example.com/webhook",`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 97**: Hardcoded value detected on line 97 - should use settings file
- **Code**: `webhook_url="https://example.com/webhook",`
- **Fix**: Move hardcoded values to configuration files

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

*... and 2 more violations*

---

### ❌ test_configuration_policy_management_routes.py

- **Path**: `src\cloud-services\shared-services\configuration-policy-management\tests\test_configuration_policy_management_routes.py`
- **Compliance**: 52.8%
- **Total Violations**: 12
- **Processing Time**: 0.162s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 5
- **Info**: 7

#### Violations

**🟡 Rule 65: Only Use Information You're Given**
- **Line 21**: Magic number detected - use named constants
- **Code**: `= 200`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 65: Only Use Information You're Given**
- **Line 28**: Magic number detected - use named constants
- **Code**: `= 200`
- **Fix**: Replace magic numbers with named constants

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without explanation patterns
- **Code**: `AI explanations`
- **Fix**: Add explanations for AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

*... and 2 more violations*

---

### ❌ test_contracts_schema_registry_routes.py

- **Path**: `src\cloud-services\shared-services\contracts-schema-registry\tests\test_contracts_schema_registry_routes.py`
- **Compliance**: 52.8%
- **Total Violations**: 12
- **Processing Time**: 0.366s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 5
- **Info**: 7

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without explanation patterns
- **Code**: `AI explanations`
- **Fix**: Add explanations for AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

**🟡 Rule 65: Only Use Information You're Given**
- **Line 21**: Magic number detected - use named constants
- **Code**: `= 200`
- **Fix**: Replace magic numbers with named constants

*... and 2 more violations*

---

### ❌ main.py

- **Path**: `src\cloud-services\shared-services\contracts-schema-registry\main.py`
- **Compliance**: 53.3%
- **Total Violations**: 5
- **Processing Time**: 0.199s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 2
- **Info**: 3

#### Violations

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 58**: Hardcoded value detected on line 58 - should use settings file
- **Code**: `if engine.url.drivername == "sqlite":`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

---

### ❌ edge_agent_bridge.py

- **Path**: `src\shared_libs\cccs\integration\edge_agent_bridge.py`
- **Compliance**: 53.3%
- **Total Violations**: 5
- **Processing Time**: 0.056s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 2
- **Info**: 3

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without explanation patterns
- **Code**: `AI explanations`
- **Fix**: Add explanations for AI decisions

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ❌ test_receipt_service.py

- **Path**: `src\cloud-services\shared-services\budgeting-rate-limiting-cost-observability\tests\test_receipt_service.py`
- **Compliance**: 53.9%
- **Total Violations**: 13
- **Processing Time**: 0.092s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 5
- **Info**: 8

#### Violations

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 54**: Hardcoded value detected on line 54 - should use settings file
- **Code**: `limit_value=100,`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 60**: Hardcoded value detected on line 60 - should use settings file
- **Code**: `assert receipt["gate_id"] == "rate-limit-check"`
- **Fix**: Move hardcoded values to configuration files

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without explanation patterns
- **Code**: `AI explanations`
- **Fix**: Add explanations for AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

*... and 3 more violations*

---

### ❌ test_key_management_service_routes.py

- **Path**: `src\cloud-services\shared-services\key-management-service\tests\test_key_management_service_routes.py`
- **Compliance**: 53.9%
- **Total Violations**: 13
- **Processing Time**: 0.121s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 5
- **Info**: 8

#### Violations

**🟡 Rule 65: Only Use Information You're Given**
- **Line 21**: Magic number detected - use named constants
- **Code**: `= 200`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 65: Only Use Information You're Given**
- **Line 29**: Magic number detected - use named constants
- **Code**: `= 200`
- **Fix**: Replace magic numbers with named constants

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without explanation patterns
- **Code**: `AI explanations`
- **Fix**: Add explanations for AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without version tracking
- **Code**: `AI version tracking`
- **Fix**: Track AI model versions for transparency

*... and 3 more violations*

---

### ❌ 001_initial_schema.py

- **Path**: `src\cloud-services\shared-services\configuration-policy-management\database\migrations\versions\001_initial_schema.py`
- **Compliance**: 54.2%
- **Total Violations**: 8
- **Processing Time**: 0.157s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 3
- **Info**: 5

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without explanation patterns
- **Code**: `AI explanations`
- **Fix**: Add explanations for AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ❌ routes.py

- **Path**: `src\cloud-services\shared-services\configuration-policy-management\routes.py`
- **Compliance**: 55.6%
- **Total Violations**: 6
- **Processing Time**: 0.081s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 2
- **Info**: 4

#### Violations

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 252**: Hardcoded value detected on line 252 - should use settings file
- **Code**: `policy_id: str = Path(..., description="Policy identifier"),`
- **Fix**: Move hardcoded values to configuration files

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ❌ models.py

- **Path**: `src\cloud-services\shared-services\configuration-policy-management\database\models.py`
- **Compliance**: 55.6%
- **Total Violations**: 6
- **Processing Time**: 0.311s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 2
- **Info**: 4

#### Violations

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ❌ 001_initial_schema.py

- **Path**: `src\cloud-services\shared-services\contracts-schema-registry\database\migrations\versions\001_initial_schema.py`
- **Compliance**: 55.6%
- **Total Violations**: 9
- **Processing Time**: 0.114s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 3
- **Info**: 6

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without explanation patterns
- **Code**: `AI explanations`
- **Fix**: Add explanations for AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ❌ models.py

- **Path**: `src\cloud-services\shared-services\data-governance-privacy\models.py`
- **Compliance**: 55.6%
- **Total Violations**: 9
- **Processing Time**: 0.097s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 3
- **Info**: 6

#### Violations

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 190**: Hardcoded value detected on line 190 - should use settings file
- **Code**: `portability = "portability"`
- **Fix**: Move hardcoded values to configuration files

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without explanation patterns
- **Code**: `AI explanations`
- **Fix**: Add explanations for AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

**🟡 Rule 96: Be Extra Careful with Private Data**
- **Line 1**: Private data detected without encryption
- **Code**: `Private data encryption`
- **Fix**: Implement encryption for private data

**🔵 Rule 65: Only Use Information You're Given**
- **Line 204**: Assumption detected in code or comments
- **Code**: `estimate`
- **Fix**: Use only information explicitly provided

---

### ❌ connection.py

- **Path**: `src\cloud-services\shared-services\contracts-schema-registry\database\connection.py`
- **Compliance**: 55.6%
- **Total Violations**: 9
- **Processing Time**: 0.230s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 3
- **Info**: 6

#### Violations

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 59**: Hardcoded value detected on line 59 - should use settings file
- **Code**: `connect_args={"check_same_thread": False} if "sqlite" in database_url else {}`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 68**: Hardcoded value detected on line 68 - should use settings file
- **Code**: `max_overflow=20,`
- **Fix**: Move hardcoded values to configuration files

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without version tracking
- **Code**: `AI version tracking`
- **Fix**: Track AI model versions for transparency

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ❌ mock_hsm.py

- **Path**: `src\cloud-services\shared-services\key-management-service\hsm\mock_hsm.py`
- **Compliance**: 55.6%
- **Total Violations**: 9
- **Processing Time**: 0.144s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 3
- **Info**: 6

#### Violations

**🟡 Rule 65: Only Use Information You're Given**
- **Line 81**: Magic number detected - use named constants
- **Code**: `=65537`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 65: Only Use Information You're Given**
- **Line 82**: Magic number detected - use named constants
- **Code**: `=2048`
- **Fix**: Replace magic numbers with named constants

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without version tracking
- **Code**: `AI version tracking`
- **Fix**: Track AI model versions for transparency

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ❌ types.py

- **Path**: `src\shared_libs\cccs\types.py`
- **Compliance**: 55.6%
- **Total Violations**: 6
- **Processing Time**: 0.068s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 2
- **Info**: 4

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without explanation patterns
- **Code**: `AI explanations`
- **Fix**: Add explanations for AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ❌ test_cost_service.py

- **Path**: `src\cloud-services\shared-services\budgeting-rate-limiting-cost-observability\tests\test_cost_service.py`
- **Compliance**: 56.4%
- **Total Violations**: 13
- **Processing Time**: 0.515s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 4
- **Info**: 9

#### Violations

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 102**: Hardcoded value detected on line 102 - should use settings file
- **Code**: `report_type="summary",`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 107**: Hardcoded value detected on line 107 - should use settings file
- **Code**: `assert report["report_type"] == "summary"`
- **Fix**: Move hardcoded values to configuration files

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without explanation patterns
- **Code**: `AI explanations`
- **Fix**: Add explanations for AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without version tracking
- **Code**: `AI version tracking`
- **Fix**: Track AI model versions for transparency

*... and 3 more violations*

---

### ❌ test_identity_access_management_service.py

- **Path**: `src\cloud-services\shared-services\identity-access-management\tests\test_identity_access_management_service.py`
- **Compliance**: 56.4%
- **Total Violations**: 13
- **Processing Time**: 0.250s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 4
- **Info**: 9

#### Violations

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 62**: Hardcoded value detected on line 62 - should use settings file
- **Code**: `assert evaluator.map_org_role("executive") == "admin"`
- **Fix**: Move hardcoded values to configuration files

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without explanation patterns
- **Code**: `AI explanations`
- **Fix**: Add explanations for AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without version tracking
- **Code**: `AI version tracking`
- **Fix**: Track AI model versions for transparency

*... and 3 more violations*

---

### ❌ errors.py

- **Path**: `src\cloud-services\shared-services\contracts-schema-registry\errors.py`
- **Compliance**: 56.7%
- **Total Violations**: 10
- **Processing Time**: 0.041s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 3
- **Info**: 7

#### Violations

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 51**: Hardcoded value detected on line 51 - should use settings file
- **Code**: `RATE_LIMITED = "RATE_LIMITED"`
- **Fix**: Move hardcoded values to configuration files

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ❌ __init__.py

- **Path**: `src\configuration_policy_management\__init__.py`
- **Compliance**: 56.7%
- **Total Violations**: 10
- **Processing Time**: 0.093s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 3
- **Info**: 7

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without explanation patterns
- **Code**: `AI explanations`
- **Fix**: Add explanations for AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without version tracking
- **Code**: `AI version tracking`
- **Fix**: Track AI model versions for transparency

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ❌ exceptions.py

- **Path**: `src\shared_libs\cccs\exceptions.py`
- **Compliance**: 56.7%
- **Total Violations**: 10
- **Processing Time**: 0.092s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 3
- **Info**: 7

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without explanation patterns
- **Code**: `AI explanations`
- **Fix**: Add explanations for AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ❌ dependencies.py

- **Path**: `src\cloud-services\shared-services\budgeting-rate-limiting-cost-observability\dependencies.py`
- **Compliance**: 57.1%
- **Total Violations**: 7
- **Processing Time**: 0.159s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 2
- **Info**: 5

#### Violations

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 300**: Hardcoded value detected on line 300 - should use settings file
- **Code**: `if "system_architect" in roles and resource == "rate_limit":`
- **Fix**: Move hardcoded values to configuration files

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without version tracking
- **Code**: `AI version tracking`
- **Fix**: Track AI model versions for transparency

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ❌ event_service.py

- **Path**: `src\cloud-services\shared-services\budgeting-rate-limiting-cost-observability\services\event_service.py`
- **Compliance**: 57.1%
- **Total Violations**: 7
- **Processing Time**: 0.064s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 2
- **Info**: 5

#### Violations

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 151**: Hardcoded value detected on line 151 - should use settings file
- **Code**: `event_type="rate_limit_violated",`
- **Fix**: Move hardcoded values to configuration files

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without version tracking
- **Code**: `AI version tracking`
- **Fix**: Track AI model versions for transparency

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ❌ services.py

- **Path**: `src\cloud-services\shared-services\data-governance-privacy\services.py`
- **Compliance**: 57.1%
- **Total Violations**: 7
- **Processing Time**: 0.168s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 2
- **Info**: 5

#### Violations

**🟡 Rule 65: Only Use Information You're Given**
- **Line 41**: Magic number detected - use named constants
- **Code**: `= 1000`
- **Fix**: Replace magic numbers with named constants

**🔵 Rule 65: Only Use Information You're Given**
- **Line 506**: Assumption detected in code or comments
- **Code**: `estimate`
- **Fix**: Use only information explicitly provided

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without explanation patterns
- **Code**: `AI explanations`
- **Fix**: Add explanations for AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ❌ runtime.py

- **Path**: `src\shared_libs\cccs\policy\runtime.py`
- **Compliance**: 57.1%
- **Total Violations**: 7
- **Processing Time**: 0.048s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 2
- **Info**: 5

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without explanation patterns
- **Code**: `AI explanations`
- **Fix**: Add explanations for AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

---

### ❌ routes.py

- **Path**: `src\cloud-services\shared-services\ollama-ai-agent\routes.py`
- **Compliance**: 57.1%
- **Total Violations**: 7
- **Processing Time**: 0.260s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 2
- **Info**: 5

#### Violations

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

**🟡 Rule 65: Only Use Information You're Given**
- **Line 77**: Magic number detected - use named constants
- **Code**: `=500`
- **Fix**: Replace magic numbers with named constants

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ❌ service.py

- **Path**: `src\shared_libs\cccs\redaction\service.py`
- **Compliance**: 57.1%
- **Total Violations**: 7
- **Processing Time**: 0.056s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 2
- **Info**: 5

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without explanation patterns
- **Code**: `AI explanations`
- **Fix**: Add explanations for AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

---

### ❌ __init__.py

- **Path**: `src\deployment_infrastructure\__init__.py`
- **Compliance**: 57.6%
- **Total Violations**: 11
- **Processing Time**: 0.070s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 3
- **Info**: 8

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without explanation patterns
- **Code**: `AI explanations`
- **Fix**: Add explanations for AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without version tracking
- **Code**: `AI version tracking`
- **Fix**: Track AI model versions for transparency

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

*... and 1 more violations*

---

### ❌ __init__.py

- **Path**: `src\key_management_service\__init__.py`
- **Compliance**: 57.6%
- **Total Violations**: 11
- **Processing Time**: 0.081s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 3
- **Info**: 8

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without explanation patterns
- **Code**: `AI explanations`
- **Fix**: Add explanations for AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without version tracking
- **Code**: `AI version tracking`
- **Fix**: Track AI model versions for transparency

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

*... and 1 more violations*

---

### ❌ __init__.py

- **Path**: `src\contracts_schema_registry\__init__.py`
- **Compliance**: 57.6%
- **Total Violations**: 11
- **Processing Time**: 0.089s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 3
- **Info**: 8

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without explanation patterns
- **Code**: `AI explanations`
- **Fix**: Add explanations for AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without version tracking
- **Code**: `AI version tracking`
- **Fix**: Track AI model versions for transparency

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

*... and 1 more violations*

---

### ❌ versioning.py

- **Path**: `src\shared_libs\cccs\versioning.py`
- **Compliance**: 57.6%
- **Total Violations**: 11
- **Processing Time**: 0.039s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 3
- **Info**: 8

#### Violations

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without explanation patterns
- **Code**: `AI explanations`
- **Fix**: Add explanations for AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

*... and 1 more violations*

---

### ❌ __init__.py

- **Path**: `src\identity_access_management\__init__.py`
- **Compliance**: 57.6%
- **Total Violations**: 11
- **Processing Time**: 0.178s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 3
- **Info**: 8

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without explanation patterns
- **Code**: `AI explanations`
- **Fix**: Add explanations for AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without version tracking
- **Code**: `AI version tracking`
- **Fix**: Track AI model versions for transparency

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

*... and 1 more violations*

---

### ❌ session.py

- **Path**: `src\cloud-services\shared-services\budgeting-rate-limiting-cost-observability\database\session.py`
- **Compliance**: 58.3%
- **Total Violations**: 8
- **Processing Time**: 0.194s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 2
- **Info**: 6

#### Violations

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 39**: Hardcoded value detected on line 39 - should use settings file
- **Code**: `max_overflow=20,`
- **Fix**: Move hardcoded values to configuration files

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without version tracking
- **Code**: `AI version tracking`
- **Fix**: Track AI model versions for transparency

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ❌ quota_service.py

- **Path**: `src\cloud-services\shared-services\budgeting-rate-limiting-cost-observability\services\quota_service.py`
- **Compliance**: 58.3%
- **Total Violations**: 8
- **Processing Time**: 0.140s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 2
- **Info**: 6

#### Violations

**🟡 Rule 65: Only Use Information You're Given**
- **Line 112**: Magic number detected - use named constants
- **Code**: `= 100`
- **Fix**: Replace magic numbers with named constants

**🔵 Rule 65: Only Use Information You're Given**
- **Line 180**: Assumption detected in code or comments
- **Code**: `could`
- **Fix**: Use only information explicitly provided

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without version tracking
- **Code**: `AI version tracking`
- **Fix**: Track AI model versions for transparency

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ❌ dependencies.py

- **Path**: `src\cloud-services\shared-services\configuration-policy-management\dependencies.py`
- **Compliance**: 58.3%
- **Total Violations**: 4
- **Processing Time**: 0.128s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 3

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ❌ main.py

- **Path**: `src\cloud-services\shared-services\configuration-policy-management\main.py`
- **Compliance**: 58.3%
- **Total Violations**: 4
- **Processing Time**: 0.196s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 3

#### Violations

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

---

### ❌ test_configuration_policy_management_service.py

- **Path**: `src\cloud-services\shared-services\configuration-policy-management\tests\test_configuration_policy_management_service.py`
- **Compliance**: 58.3%
- **Total Violations**: 12
- **Processing Time**: 0.236s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 3
- **Info**: 9

#### Violations

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without explanation patterns
- **Code**: `AI explanations`
- **Fix**: Add explanations for AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without version tracking
- **Code**: `AI version tracking`
- **Fix**: Track AI model versions for transparency

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

*... and 2 more violations*

---

### ❌ services.py

- **Path**: `src\cloud-services\shared-services\deployment-infrastructure\services.py`
- **Compliance**: 58.3%
- **Total Violations**: 20
- **Processing Time**: 0.053s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 5
- **Info**: 15

#### Violations

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 70**: Hardcoded value detected on line 70 - should use settings file
- **Code**: `estimated_minutes = 2`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 72**: Hardcoded value detected on line 72 - should use settings file
- **Code**: `estimated_minutes = 10`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 74**: Hardcoded value detected on line 74 - should use settings file
- **Code**: `estimated_minutes = 15`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 77**: Hardcoded value detected on line 77 - should use settings file
- **Code**: `estimated_minutes += 2  # Additional time for specific service`
- **Fix**: Move hardcoded values to configuration files

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

**🔵 Rule 65: Only Use Information You're Given**
- **Line 233**: Assumption detected in code or comments
- **Code**: `might`
- **Fix**: Use only information explicitly provided

**🔵 Rule 65: Only Use Information You're Given**
- **Line 68**: Assumption detected in code or comments
- **Code**: `Estimate`
- **Fix**: Use only information explicitly provided

*... and 10 more violations*

---

### ❌ main.py

- **Path**: `src\cloud-services\shared-services\deployment-infrastructure\main.py`
- **Compliance**: 58.3%
- **Total Violations**: 4
- **Processing Time**: 0.148s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 3

#### Violations

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

---

### ❌ main.py

- **Path**: `src\cloud-services\shared-services\key-management-service\main.py`
- **Compliance**: 58.3%
- **Total Violations**: 4
- **Processing Time**: 0.061s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 3

#### Violations

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

---

### ❌ main.py

- **Path**: `src\cloud-services\shared-services\identity-access-management\main.py`
- **Compliance**: 58.3%
- **Total Violations**: 4
- **Processing Time**: 0.220s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 3

#### Violations

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

---

### ❌ __init__.py

- **Path**: `src\data_governance_privacy\__init__.py`
- **Compliance**: 58.3%
- **Total Violations**: 12
- **Processing Time**: 0.155s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 3
- **Info**: 9

#### Violations

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without explanation patterns
- **Code**: `AI explanations`
- **Fix**: Add explanations for AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without version tracking
- **Code**: `AI version tracking`
- **Fix**: Track AI model versions for transparency

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

*... and 2 more violations*

---

### ❌ test_quota_service.py

- **Path**: `src\cloud-services\shared-services\budgeting-rate-limiting-cost-observability\tests\test_quota_service.py`
- **Compliance**: 59.0%
- **Total Violations**: 13
- **Processing Time**: 0.061s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 3
- **Info**: 10

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without explanation patterns
- **Code**: `AI explanations`
- **Fix**: Add explanations for AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without version tracking
- **Code**: `AI version tracking`
- **Fix**: Track AI model versions for transparency

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

*... and 3 more violations*

---

### ❌ test_contracts_schema_registry_service.py

- **Path**: `src\cloud-services\shared-services\contracts-schema-registry\tests\test_contracts_schema_registry_service.py`
- **Compliance**: 59.0%
- **Total Violations**: 13
- **Processing Time**: 0.186s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 3
- **Info**: 10

#### Violations

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without explanation patterns
- **Code**: `AI explanations`
- **Fix**: Add explanations for AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without version tracking
- **Code**: `AI version tracking`
- **Fix**: Track AI model versions for transparency

*... and 3 more violations*

---

### ❌ test_key_management_service_service.py

- **Path**: `src\cloud-services\shared-services\key-management-service\tests\test_key_management_service_service.py`
- **Compliance**: 59.0%
- **Total Violations**: 13
- **Processing Time**: 0.116s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 3
- **Info**: 10

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without explanation patterns
- **Code**: `AI explanations`
- **Fix**: Add explanations for AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without version tracking
- **Code**: `AI version tracking`
- **Fix**: Track AI model versions for transparency

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

*... and 3 more violations*

---

### ❌ cache.py

- **Path**: `src\cloud-services\shared-services\budgeting-rate-limiting-cost-observability\utils\cache.py`
- **Compliance**: 59.3%
- **Total Violations**: 9
- **Processing Time**: 0.254s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 2
- **Info**: 7

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without version tracking
- **Code**: `AI version tracking`
- **Fix**: Track AI model versions for transparency

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

**🟡 Rule 65: Only Use Information You're Given**
- **Line 63**: Magic number detected - use named constants
- **Code**: `= 300`
- **Fix**: Replace magic numbers with named constants

---

### ❌ __init__.py

- **Path**: `src\cloud-services\shared-services\deployment-infrastructure\__init__.py`
- **Compliance**: 59.3%
- **Total Violations**: 9
- **Processing Time**: 0.038s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 2
- **Info**: 7

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ⚠️ dependencies.py

- **Path**: `src\cloud-services\shared-services\data-governance-privacy\dependencies.py`
- **Compliance**: 60.0%
- **Total Violations**: 5
- **Processing Time**: 0.155s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 4

#### Violations

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without version tracking
- **Code**: `AI version tracking`
- **Fix**: Track AI model versions for transparency

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ⚠️ dependencies.py

- **Path**: `src\cloud-services\shared-services\identity-access-management\dependencies.py`
- **Compliance**: 60.0%
- **Total Violations**: 5
- **Processing Time**: 0.089s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 4

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ⚠️ models.py

- **Path**: `src\cloud-services\shared-services\deployment-infrastructure\models.py`
- **Compliance**: 60.0%
- **Total Violations**: 10
- **Processing Time**: 0.215s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 2
- **Info**: 8

#### Violations

**🔵 Rule 65: Only Use Information You're Given**
- **Line 33**: Assumption detected in code or comments
- **Code**: `estimate`
- **Fix**: Use only information explicitly provided

**🔵 Rule 65: Only Use Information You're Given**
- **Line 33**: Assumption detected in code or comments
- **Code**: `Estimate`
- **Fix**: Use only information explicitly provided

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ⚠️ dependencies.py

- **Path**: `src\cloud-services\shared-services\key-management-service\dependencies.py`
- **Compliance**: 60.0%
- **Total Violations**: 5
- **Processing Time**: 0.214s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 4

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ⚠️ __init__.py

- **Path**: `src\cloud-services\shared-services\configuration-policy-management\database\__init__.py`
- **Compliance**: 60.6%
- **Total Violations**: 11
- **Processing Time**: 0.252s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 2
- **Info**: 9

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without version tracking
- **Code**: `AI version tracking`
- **Fix**: Track AI model versions for transparency

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

*... and 1 more violations*

---

### ⚠️ __init__.py

- **Path**: `src\cloud-services\shared-services\contracts-schema-registry\__init__.py`
- **Compliance**: 60.6%
- **Total Violations**: 11
- **Processing Time**: 0.142s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 2
- **Info**: 9

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

*... and 1 more violations*

---

### ⚠️ __init__.py

- **Path**: `src\cloud-services\shared-services\key-management-service\hsm\__init__.py`
- **Compliance**: 60.6%
- **Total Violations**: 11
- **Processing Time**: 0.038s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 2
- **Info**: 9

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without version tracking
- **Code**: `AI version tracking`
- **Fix**: Track AI model versions for transparency

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

*... and 1 more violations*

---

### ⚠️ interface.py

- **Path**: `src\cloud-services\shared-services\key-management-service\hsm\interface.py`
- **Compliance**: 60.6%
- **Total Violations**: 11
- **Processing Time**: 0.177s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 2
- **Info**: 9

#### Violations

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without version tracking
- **Code**: `AI version tracking`
- **Fix**: Track AI model versions for transparency

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

*... and 1 more violations*

---

### ⚠️ __init__.py

- **Path**: `src\cloud-services\shared-services\ollama-ai-agent\__init__.py`
- **Compliance**: 60.6%
- **Total Violations**: 11
- **Processing Time**: 0.082s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 2
- **Info**: 9

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without version tracking
- **Code**: `AI version tracking`
- **Fix**: Track AI model versions for transparency

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

*... and 1 more violations*

---

### ⚠️ test_budget_service.py

- **Path**: `src\cloud-services\shared-services\budgeting-rate-limiting-cost-observability\tests\test_budget_service.py`
- **Compliance**: 61.1%
- **Total Violations**: 18
- **Processing Time**: 0.103s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 3
- **Info**: 15

#### Violations

**🔵 Rule 65: Only Use Information You're Given**
- **Line 154**: Assumption detected in code or comments
- **Code**: `estimate`
- **Fix**: Use only information explicitly provided

**🔵 Rule 65: Only Use Information You're Given**
- **Line 182**: Assumption detected in code or comments
- **Code**: `estimate`
- **Fix**: Use only information explicitly provided

**🔵 Rule 65: Only Use Information You're Given**
- **Line 192**: Assumption detected in code or comments
- **Code**: `estimate`
- **Fix**: Use only information explicitly provided

**🔵 Rule 65: Only Use Information You're Given**
- **Line 302**: Assumption detected in code or comments
- **Code**: `estimate`
- **Fix**: Use only information explicitly provided

**🔵 Rule 65: Only Use Information You're Given**
- **Line 335**: Assumption detected in code or comments
- **Code**: `estimate`
- **Fix**: Use only information explicitly provided

**🔵 Rule 65: Only Use Information You're Given**
- **Line 343**: Assumption detected in code or comments
- **Code**: `estimate`
- **Fix**: Use only information explicitly provided

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 327**: Hardcoded value detected on line 327 - should use settings file
- **Code**: `enforcement_action="soft_limit",`
- **Fix**: Move hardcoded values to configuration files

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

*... and 8 more violations*

---

### ⚠️ dependencies.py

- **Path**: `src\cloud-services\shared-services\contracts-schema-registry\dependencies.py`
- **Compliance**: 61.1%
- **Total Violations**: 6
- **Processing Time**: 0.196s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 5

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without version tracking
- **Code**: `AI version tracking`
- **Fix**: Track AI model versions for transparency

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ⚠️ __init__.py

- **Path**: `src\cloud-services\shared-services\contracts-schema-registry\database\__init__.py`
- **Compliance**: 61.1%
- **Total Violations**: 12
- **Processing Time**: 0.080s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 2
- **Info**: 10

#### Violations

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without version tracking
- **Code**: `AI version tracking`
- **Fix**: Track AI model versions for transparency

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

*... and 2 more violations*

---

### ⚠️ transformer.py

- **Path**: `src\cloud-services\shared-services\contracts-schema-registry\compatibility\transformer.py`
- **Compliance**: 61.1%
- **Total Violations**: 6
- **Processing Time**: 0.125s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 5

#### Violations

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ⚠️ models.py

- **Path**: `src\cloud-services\shared-services\contracts-schema-registry\database\models.py`
- **Compliance**: 61.1%
- **Total Violations**: 6
- **Processing Time**: 0.129s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 5

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ⚠️ routes.py

- **Path**: `src\cloud-services\shared-services\identity-access-management\routes.py`
- **Compliance**: 61.1%
- **Total Violations**: 6
- **Processing Time**: 0.024s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 5

#### Violations

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ⚠️ test_deployment_infrastructure_service.py

- **Path**: `src\cloud-services\shared-services\deployment-infrastructure\tests\test_deployment_infrastructure_service.py`
- **Compliance**: 61.1%
- **Total Violations**: 12
- **Processing Time**: 0.059s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 2
- **Info**: 10

#### Violations

**🔵 Rule 65: Only Use Information You're Given**
- **Line 102**: Assumption detected in code or comments
- **Code**: `estimate`
- **Fix**: Use only information explicitly provided

**🔵 Rule 65: Only Use Information You're Given**
- **Line 103**: Assumption detected in code or comments
- **Code**: `estimate`
- **Fix**: Use only information explicitly provided

**🔵 Rule 65: Only Use Information You're Given**
- **Line 109**: Assumption detected in code or comments
- **Code**: `estimate`
- **Fix**: Use only information explicitly provided

**🔵 Rule 65: Only Use Information You're Given**
- **Line 110**: Assumption detected in code or comments
- **Code**: `estimate`
- **Fix**: Use only information explicitly provided

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without explanation patterns
- **Code**: `AI explanations`
- **Fix**: Add explanations for AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

*... and 2 more violations*

---

### ⚠️ routes.py

- **Path**: `src\cloud-services\shared-services\deployment-infrastructure\routes.py`
- **Compliance**: 61.1%
- **Total Violations**: 6
- **Processing Time**: 0.134s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 5

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

---

### ⚠️ main.py

- **Path**: `src\cloud-services\shared-services\ollama-ai-agent\main.py`
- **Compliance**: 61.1%
- **Total Violations**: 6
- **Processing Time**: 0.060s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 5

#### Violations

**🔵 Rule 65: Only Use Information You're Given**
- **Line 57**: Assumption detected in code or comments
- **Code**: `could`
- **Fix**: Use only information explicitly provided

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

---

### ⚠️ receipt_service.py

- **Path**: `src\cloud-services\shared-services\budgeting-rate-limiting-cost-observability\services\receipt_service.py`
- **Compliance**: 61.5%
- **Total Violations**: 13
- **Processing Time**: 0.201s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 2
- **Info**: 11

#### Violations

**🔵 Rule 65: Only Use Information You're Given**
- **Line 125**: Assumption detected in code or comments
- **Code**: `estimate`
- **Fix**: Use only information explicitly provided

**🔵 Rule 65: Only Use Information You're Given**
- **Line 142**: Assumption detected in code or comments
- **Code**: `estimate`
- **Fix**: Use only information explicitly provided

**🔵 Rule 65: Only Use Information You're Given**
- **Line 142**: Assumption detected in code or comments
- **Code**: `Estimate`
- **Fix**: Use only information explicitly provided

**🔵 Rule 65: Only Use Information You're Given**
- **Line 169**: Assumption detected in code or comments
- **Code**: `estimate`
- **Fix**: Use only information explicitly provided

**🔵 Rule 65: Only Use Information You're Given**
- **Line 169**: Assumption detected in code or comments
- **Code**: `estimate`
- **Fix**: Use only information explicitly provided

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

**🟡 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 280**: Hardcoded value detected on line 280 - should use settings file
- **Code**: `gate_id="rate-limit-check",`
- **Fix**: Move hardcoded values to configuration files

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

*... and 3 more violations*

---

### ⚠️ event_subscription_service.py

- **Path**: `src\cloud-services\shared-services\budgeting-rate-limiting-cost-observability\services\event_subscription_service.py`
- **Compliance**: 61.9%
- **Total Violations**: 7
- **Processing Time**: 0.102s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 6

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

---

### ⚠️ conftest.py

- **Path**: `src\cloud-services\shared-services\budgeting-rate-limiting-cost-observability\tests\conftest.py`
- **Compliance**: 61.9%
- **Total Violations**: 7
- **Processing Time**: 0.168s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 6

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ⚠️ __init__.py

- **Path**: `src\cloud-services\shared-services\configuration-policy-management\tests\__init__.py`
- **Compliance**: 61.9%
- **Total Violations**: 7
- **Processing Time**: 0.084s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 6

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ⚠️ connection.py

- **Path**: `src\cloud-services\shared-services\configuration-policy-management\database\connection.py`
- **Compliance**: 61.9%
- **Total Violations**: 7
- **Processing Time**: 0.234s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 6

#### Violations

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without version tracking
- **Code**: `AI version tracking`
- **Fix**: Track AI model versions for transparency

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

---

### ⚠️ avro_validator.py

- **Path**: `src\cloud-services\shared-services\contracts-schema-registry\validators\avro_validator.py`
- **Compliance**: 61.9%
- **Total Violations**: 7
- **Processing Time**: 0.025s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 6

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without version tracking
- **Code**: `AI version tracking`
- **Fix**: Track AI model versions for transparency

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ⚠️ __init__.py

- **Path**: `src\cloud-services\shared-services\contracts-schema-registry\cache\__init__.py`
- **Compliance**: 61.9%
- **Total Violations**: 7
- **Processing Time**: 0.201s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 6

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ⚠️ __init__.py

- **Path**: `src\cloud-services\shared-services\contracts-schema-registry\validators\__init__.py`
- **Compliance**: 61.9%
- **Total Violations**: 7
- **Processing Time**: 0.210s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 6

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ⚠️ __init__.py

- **Path**: `src\shared_libs\cccs\__init__.py`
- **Compliance**: 61.9%
- **Total Violations**: 7
- **Processing Time**: 0.023s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 6

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ⚠️ __init__.py

- **Path**: `src\shared_libs\cccs\config\__init__.py`
- **Compliance**: 61.9%
- **Total Violations**: 7
- **Processing Time**: 0.054s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 6

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ⚠️ __init__.py

- **Path**: `src\shared_libs\cccs\identity\__init__.py`
- **Compliance**: 61.9%
- **Total Violations**: 7
- **Processing Time**: 0.047s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 6

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ⚠️ __init__.py

- **Path**: `src\shared_libs\cccs\errors\__init__.py`
- **Compliance**: 61.9%
- **Total Violations**: 7
- **Processing Time**: 0.096s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 6

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ⚠️ __init__.py

- **Path**: `src\shared_libs\cccs\policy\__init__.py`
- **Compliance**: 61.9%
- **Total Violations**: 7
- **Processing Time**: 0.071s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 6

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ⚠️ __init__.py

- **Path**: `src\shared_libs\cccs\ratelimit\__init__.py`
- **Compliance**: 61.9%
- **Total Violations**: 7
- **Processing Time**: 0.058s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 6

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ⚠️ __init__.py

- **Path**: `src\shared_libs\cccs\redaction\__init__.py`
- **Compliance**: 61.9%
- **Total Violations**: 7
- **Processing Time**: 0.050s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 6

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ⚠️ __init__.py

- **Path**: `src\shared_libs\cccs\receipts\__init__.py`
- **Compliance**: 61.9%
- **Total Violations**: 7
- **Processing Time**: 0.059s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 6

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ⚠️ budget_service.py

- **Path**: `src\cloud-services\shared-services\budgeting-rate-limiting-cost-observability\services\budget_service.py`
- **Compliance**: 62.3%
- **Total Violations**: 23
- **Processing Time**: 0.168s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 3
- **Info**: 20

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without version tracking
- **Code**: `AI version tracking`
- **Fix**: Track AI model versions for transparency

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

**🟡 Rule 65: Only Use Information You're Given**
- **Line 248**: Magic number detected - use named constants
- **Code**: `=365`
- **Fix**: Replace magic numbers with named constants

**🟡 Rule 65: Only Use Information You're Given**
- **Line 368**: Magic number detected - use named constants
- **Code**: `= 100`
- **Fix**: Replace magic numbers with named constants

**🔵 Rule 65: Only Use Information You're Given**
- **Line 540**: Assumption detected in code or comments
- **Code**: `could`
- **Fix**: Use only information explicitly provided

**🔵 Rule 65: Only Use Information You're Given**
- **Line 172**: Assumption detected in code or comments
- **Code**: `estimate`
- **Fix**: Use only information explicitly provided

*... and 13 more violations*

---

### ⚠️ __init__.py

- **Path**: `src\__init__.py`
- **Compliance**: 62.5%
- **Total Violations**: 8
- **Processing Time**: 0.148s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 7

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ⚠️ __init__.py

- **Path**: `src\budgeting_rate_limiting_cost_observability\__init__.py`
- **Compliance**: 62.5%
- **Total Violations**: 8
- **Processing Time**: 0.148s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 7

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ⚠️ __init__.py

- **Path**: `src\cloud-services\shared-services\budgeting-rate-limiting-cost-observability\__init__.py`
- **Compliance**: 62.5%
- **Total Violations**: 8
- **Processing Time**: 0.101s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 7

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ⚠️ __init__.py

- **Path**: `src\cloud-services\shared-services\budgeting-rate-limiting-cost-observability\utils\__init__.py`
- **Compliance**: 62.5%
- **Total Violations**: 8
- **Processing Time**: 0.080s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 7

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ⚠️ transactions.py

- **Path**: `src\cloud-services\shared-services\budgeting-rate-limiting-cost-observability\utils\transactions.py`
- **Compliance**: 62.5%
- **Total Violations**: 8
- **Processing Time**: 0.145s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 7

#### Violations

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without version tracking
- **Code**: `AI version tracking`
- **Fix**: Track AI model versions for transparency

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ⚠️ __init__.py

- **Path**: `src\cloud-services\shared-services\budgeting-rate-limiting-cost-observability\tests\__init__.py`
- **Compliance**: 62.5%
- **Total Violations**: 8
- **Processing Time**: 0.162s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 7

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ⚠️ env.py

- **Path**: `src\cloud-services\shared-services\configuration-policy-management\database\migrations\env.py`
- **Compliance**: 62.5%
- **Total Violations**: 8
- **Processing Time**: 0.096s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 7

#### Violations

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ⚠️ __init__.py

- **Path**: `src\cloud-services\shared-services\configuration-policy-management\database\migrations\__init__.py`
- **Compliance**: 62.5%
- **Total Violations**: 8
- **Processing Time**: 0.233s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 7

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

---

### ⚠️ __init__.py

- **Path**: `src\cloud-services\shared-services\contracts-schema-registry\analytics\__init__.py`
- **Compliance**: 62.5%
- **Total Violations**: 8
- **Processing Time**: 0.117s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 7

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ⚠️ __init__.py

- **Path**: `src\cloud-services\shared-services\contracts-schema-registry\compatibility\__init__.py`
- **Compliance**: 62.5%
- **Total Violations**: 8
- **Processing Time**: 0.060s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 7

#### Violations

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ⚠️ env.py

- **Path**: `src\cloud-services\shared-services\contracts-schema-registry\database\migrations\env.py`
- **Compliance**: 62.5%
- **Total Violations**: 8
- **Processing Time**: 0.051s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 7

#### Violations

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ⚠️ manager.py

- **Path**: `src\cloud-services\shared-services\contracts-schema-registry\templates\manager.py`
- **Compliance**: 62.5%
- **Total Violations**: 8
- **Processing Time**: 0.239s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 7

#### Violations

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without version tracking
- **Code**: `AI version tracking`
- **Fix**: Track AI model versions for transparency

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ⚠️ __init__.py

- **Path**: `src\cloud-services\shared-services\contracts-schema-registry\templates\__init__.py`
- **Compliance**: 62.5%
- **Total Violations**: 8
- **Processing Time**: 0.242s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 7

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ⚠️ __init__.py

- **Path**: `src\cloud-services\shared-services\contracts-schema-registry\tests\__init__.py`
- **Compliance**: 62.5%
- **Total Violations**: 8
- **Processing Time**: 0.267s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 7

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ⚠️ __init__.py

- **Path**: `src\cloud-services\shared-services\deployment-infrastructure\tests\__init__.py`
- **Compliance**: 62.5%
- **Total Violations**: 8
- **Processing Time**: 0.063s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 7

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ⚠️ __init__.py

- **Path**: `src\cloud-services\shared-services\identity-access-management\tests\__init__.py`
- **Compliance**: 62.5%
- **Total Violations**: 8
- **Processing Time**: 0.098s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 7

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ⚠️ __init__.py

- **Path**: `src\cloud-services\shared-services\key-management-service\__init__.py`
- **Compliance**: 62.5%
- **Total Violations**: 8
- **Processing Time**: 0.178s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 7

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ⚠️ __init__.py

- **Path**: `src\cloud-services\shared-services\key-management-service\tests\__init__.py`
- **Compliance**: 62.5%
- **Total Violations**: 8
- **Processing Time**: 0.217s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 7

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ⚠️ __init__.py

- **Path**: `src\shared_libs\__init__.py`
- **Compliance**: 62.5%
- **Total Violations**: 8
- **Processing Time**: 0.129s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 7

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ⚠️ __init__.py

- **Path**: `src\shared_libs\cccs\observability\__init__.py`
- **Compliance**: 62.5%
- **Total Violations**: 8
- **Processing Time**: 0.042s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 7

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ⚠️ __init__.py

- **Path**: `src\shared_libs\cccs\adapters\__init__.py`
- **Compliance**: 62.5%
- **Total Violations**: 8
- **Processing Time**: 0.135s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 7

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ⚠️ taxonomy.py

- **Path**: `src\shared_libs\cccs\errors\taxonomy.py`
- **Compliance**: 62.5%
- **Total Violations**: 8
- **Processing Time**: 0.126s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 7

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

---

### ⚠️ __init__.py

- **Path**: `src\shared_libs\cccs\integration\__init__.py`
- **Compliance**: 62.5%
- **Total Violations**: 8
- **Processing Time**: 0.096s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 7

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ⚠️ main.py

- **Path**: `src\cloud-services\shared-services\data-governance-privacy\main.py`
- **Compliance**: 63.0%
- **Total Violations**: 9
- **Processing Time**: 0.133s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 8

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 77: Keep Good Logs**
- **Line 1**: No logging patterns detected
- **Code**: `Logging`
- **Fix**: Add proper logging for monitoring and debugging

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

---

### ⚠️ routes.py

- **Path**: `src\cloud-services\shared-services\data-governance-privacy\routes.py`
- **Compliance**: 63.0%
- **Total Violations**: 9
- **Processing Time**: 0.120s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 8

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without explanation patterns
- **Code**: `AI explanations`
- **Fix**: Add explanations for AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without version tracking
- **Code**: `AI version tracking`
- **Fix**: Track AI model versions for transparency

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

**🔵 Rule 65: Only Use Information You're Given**
- **Line 267**: Assumption detected in code or comments
- **Code**: `estimate`
- **Fix**: Use only information explicitly provided

**🔵 Rule 65: Only Use Information You're Given**
- **Line 267**: Assumption detected in code or comments
- **Code**: `estimate`
- **Fix**: Use only information explicitly provided

---

### ⚠️ protobuf_validator.py

- **Path**: `src\cloud-services\shared-services\contracts-schema-registry\validators\protobuf_validator.py`
- **Compliance**: 63.0%
- **Total Violations**: 9
- **Processing Time**: 0.220s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 8

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without version tracking
- **Code**: `AI version tracking`
- **Fix**: Track AI model versions for transparency

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

**🔵 Rule 65: Only Use Information You're Given**
- **Line 57**: Assumption detected in code or comments
- **Code**: `Assume`
- **Fix**: Use only information explicitly provided

**🔵 Rule 65: Only Use Information You're Given**
- **Line 72**: Assumption detected in code or comments
- **Code**: `Might`
- **Fix**: Use only information explicitly provided

---

### ⚠️ __init__.py

- **Path**: `src\cloud-services\shared-services\data-governance-privacy\database\__init__.py`
- **Compliance**: 63.6%
- **Total Violations**: 11
- **Processing Time**: 0.154s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 1
- **Info**: 10

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🟡 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without confidence reporting
- **Code**: `AI confidence`
- **Fix**: Add confidence levels to AI decisions

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without version tracking
- **Code**: `AI version tracking`
- **Fix**: Track AI model versions for transparency

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

*... and 1 more violations*

---

### ⚠️ __init__.py

- **Path**: `src\cloud-services\shared-services\budgeting-rate-limiting-cost-observability\services\__init__.py`
- **Compliance**: 66.7%
- **Total Violations**: 6
- **Processing Time**: 0.104s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 0
- **Info**: 6

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ⚠️ __init__.py

- **Path**: `src\cloud-services\shared-services\configuration-policy-management\__init__.py`
- **Compliance**: 66.7%
- **Total Violations**: 5
- **Processing Time**: 0.227s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 0
- **Info**: 5

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ⚠️ checker.py

- **Path**: `src\cloud-services\shared-services\contracts-schema-registry\compatibility\checker.py`
- **Compliance**: 66.7%
- **Total Violations**: 5
- **Processing Time**: 0.089s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 0
- **Info**: 5

#### Violations

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ⚠️ models.py

- **Path**: `src\cloud-services\shared-services\data-governance-privacy\database\models.py`
- **Compliance**: 66.7%
- **Total Violations**: 6
- **Processing Time**: 0.212s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 0
- **Info**: 6

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No audit trail patterns detected
- **Code**: `Audit trail`
- **Fix**: Add audit trails for important operations

**🔵 Rule 71: Be Honest About AI Decisions**
- **Line 1**: AI code detected without uncertainty handling
- **Code**: `AI uncertainty`
- **Fix**: Handle and report AI uncertainty appropriately

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ⚠️ __init__.py

- **Path**: `src\cloud-services\shared-services\identity-access-management\__init__.py`
- **Compliance**: 66.7%
- **Total Violations**: 6
- **Processing Time**: 0.231s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 0
- **Info**: 6

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No structured logging detected
- **Code**: `Structured logging`
- **Fix**: Use structured logging for better record keeping

**🔵 Rule 77: Keep Good Logs**
- **Line 1**: No log level usage detected
- **Code**: `Log levels`
- **Fix**: Use appropriate log levels for different types of messages

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ⚠️ service.py

- **Path**: `src\shared_libs\cccs\config\service.py`
- **Compliance**: 66.7%
- **Total Violations**: 3
- **Processing Time**: 0.029s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 0
- **Info**: 3

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

---

### ⚠️ service.py

- **Path**: `src\shared_libs\cccs\observability\service.py`
- **Compliance**: 66.7%
- **Total Violations**: 5
- **Processing Time**: 0.058s

#### Violations by Severity

- **Errors**: 0
- **Warnings**: 0
- **Info**: 5

#### Violations

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No settings file usage detected
- **Code**: `Settings usage`
- **Fix**: Use configuration files instead of hardcoded values

**🔵 Rule 67: Use Settings Files, Not Hardcoded Numbers**
- **Line 1**: No environment variable usage detected
- **Code**: `Environment variables`
- **Fix**: Use environment variables for configuration

**🔵 Rule 74: Learn from Mistakes**
- **Line 1**: No learning from mistakes patterns detected
- **Code**: `Learning patterns`
- **Fix**: Add mechanisms to learn from mistakes and improve over time

**🔵 Rule 81: Be Fair to Everyone**
- **Line 1**: No fairness or accessibility patterns detected
- **Code**: `Fairness and accessibility`
- **Fix**: Add accessibility features and ensure fair treatment for all users

**🔵 Rule 87: Be Smart About Data**
- **Line 1**: Data operations detected without optimization
- **Code**: `Data optimization`
- **Fix**: Consider data optimization techniques

---
