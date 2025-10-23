# Enhanced Rule Consistency Verification

## Overview

The Enhanced Rule Consistency Verification system in `tools/rule_manager.py` provides comprehensive rule management across **all 5 sources**: Markdown, Database, JSON Export, Config, and Pre-Implementation Hooks. This system ensures consistency and synchronization across all rule storage and enforcement mechanisms.

## 🎯 **5 Sources Managed**

| Source | Path | Purpose | Read/Write |
|--------|------|---------|------------|
| **Markdown** | `docs/architecture/ZeroUI2.0_Master_Constitution.md` | Rule content and definitions | Read-only |
| **Database** | `config/constitution_rules.db` | Rule metadata and status | Read/Write |
| **JSON Export** | `config/constitution_rules.json` | External consumption | Read/Write |
| **Config** | `config/constitution_config.json` | Application configuration | Read/Write |
| **Hooks** | `config/hook_config.json` | Pre-implementation hooks | Read/Write |

## 🔧 **Key Features**

### **1. Comprehensive Source Checking**
- Verifies rule status across all 5 sources
- Identifies inconsistencies and conflicts
- Provides detailed source status information

### **2. Intelligent Conflict Resolution**
- **Majority Vote**: Uses majority enabled status across sources
- **Tie Breaking**: Handles cases where sources are evenly split
- **Priority Order**: Database > Config > JSON > Hooks > Markdown
- **Automatic Sync**: Fixes inconsistencies automatically

### **3. Enhanced Rule Management**
- Enable/disable rules across all sources
- Selective source updates with `--sources` flag
- Bulk operations for all rules
- Detailed status reporting

## 📋 **CLI Commands**

### **Rule Status Checking**
```bash
# Check status of a specific rule across all 5 sources
python tools/rule_manager.py --status-rule 150

# Check status of all rules
python tools/rule_manager.py --status
```

### **Rule Management**
```bash
# Enable rule across all sources (including hooks)
python tools/rule_manager.py --enable-rule 150

# Disable rule with reason
python tools/rule_manager.py --disable-rule 150 --reason "Too restrictive"

# Enable rule in specific sources only
python tools/rule_manager.py --enable-rule 150 --sources database config hooks

# Disable rule in specific sources
python tools/rule_manager.py --disable-rule 150 --sources database json_export hooks
```

### **Bulk Operations**
```bash
# Enable all rules across all sources
python tools/rule_manager.py --enable-all

# Disable all rules with reason
python tools/rule_manager.py --disable-all --reason "Maintenance mode"

# Enable all rules in specific sources
python tools/rule_manager.py --enable-all --sources database config hooks
```

### **Synchronization**
```bash
# Sync all 5 sources to fix inconsistencies
python tools/rule_manager.py --sync-all

# Sync specific sources only
python tools/rule_manager.py --sync-all --sources database config json_export hooks
```

## 🔍 **Enhanced Status Reporting**

### **Individual Rule Status**
```
Rule 150:
  Markdown exists: Yes
  Database enabled: True
  JSON export enabled: False
  Config enabled: True
  Hooks enabled: True
  Consistent: No
  Sources: {
    "sources_status": {...},
    "enabled_values": [True, False, True, True],
    "majority_enabled": True
  }
```

### **Sync Results**
```
SYNC ALL SOURCES RESULTS:
==================================================
Total rules: 280
Inconsistent rules: 15
Fixed inconsistencies: 12
Unresolved: 3

Source Status:
  Database: 280 rules (268 enabled, 12 disabled)
  Config: 280 rules (268 enabled, 12 disabled)
  JSON Export: 280 rules (268 enabled, 12 disabled)
  Hooks: 280 rules (268 enabled, 12 disabled)
  Markdown: 280 rules (read-only)
```

## 🏗️ **Architecture**

### **RuleStatus Dataclass**
```python
@dataclass
class RuleStatus:
    """Represents the status of a rule across all sources"""
    rule_number: int
    markdown_exists: bool
    database_enabled: Optional[bool]
    json_export_enabled: Optional[bool]
    config_enabled: Optional[bool]
    hooks_enabled: Optional[bool]  # NEW: Pre-implementation hooks
    consistent: bool
    sources: Dict[str, Any]
```

### **Enhanced Consistency Verification**
```python
def _verify_consistency_across_all_sources(self, rule_number: int) -> Dict[str, Any]:
    """Enhanced consistency verification for all 5 sources including hooks."""
    # Check all 5 sources
    # Determine consistency
    # Calculate majority vote
    # Return detailed status
```

### **Intelligent Conflict Resolution**
```python
def _get_majority_enabled_status(self, enabled_values: List[bool]) -> Optional[bool]:
    """Determine majority enabled status from list of boolean values."""
    # Count True vs False
    # Return majority or None for ties
```

## 🎯 **Rule Categories and Hooks Mapping**

| Rule Range | Category | Hook Category |
|------------|----------|---------------|
| 1-75 | Basic Work | `HookCategory.BASIC_WORK` |
| 76-99 | Code Review | `HookCategory.CODE_REVIEW` |
| 100-131 | Security & Privacy | `HookCategory.SECURITY_PRIVACY` |
| 132-149 | Logging | `HookCategory.LOGGING` |
| 150-180 | Error Handling | `HookCategory.ERROR_HANDLING` |
| 181-215 | TypeScript | `HookCategory.TYPESCRIPT` |
| 216-228 | Storage Governance | `HookCategory.STORAGE_GOVERNANCE` |
| 232-252 | GSMD | `HookCategory.GSMD` |
| 253-280 | Simple Readability | `HookCategory.SIMPLE_READABILITY` |

## 🔄 **Sync Process**

### **1. Consistency Verification**
- Check each rule across all 5 sources
- Identify discrepancies in enabled status
- Calculate majority vote for conflict resolution

### **2. Conflict Resolution**
- **Majority Vote**: Use majority enabled status
- **Tie Breaking**: Use priority order if tied
- **Automatic Fix**: Apply majority status to all sources

### **3. Source Priority Order**
1. **Database** - Highest priority (primary storage)
2. **Config** - Second priority (application settings)
3. **JSON Export** - Third priority (external consumption)
4. **Hooks** - Fourth priority (pre-implementation enforcement)
5. **Markdown** - Lowest priority (read-only content)

## 🚀 **Usage Examples**

### **Development Environment**
```bash
# Disable strict rules for prototyping
python tools/rule_manager.py --disable-rule 42 --reason "Prototyping phase"
python tools/rule_manager.py --disable-rule 90 --reason "Quick development"

# Check what's disabled
python tools/rule_manager.py --status-rule 42
```

### **Production Environment**
```bash
# Enable all rules for production
python tools/rule_manager.py --enable-all --reason "Production deployment"

# Sync all sources to ensure consistency
python tools/rule_manager.py --sync-all
```

### **Testing Specific Rules**
```bash
# Test individual rules
python tools/rule_manager.py --disable-rule 150 --reason "Testing without this rule"
python tools/rule_manager.py --enable-rule 150 --reason "Rule works correctly"

# Check consistency
python tools/rule_manager.py --status-rule 150
```

### **Selective Source Updates**
```bash
# Update only hooks configuration
python tools/rule_manager.py --enable-rule 200 --sources hooks

# Update database and hooks only
python tools/rule_manager.py --disable-rule 100 --sources database hooks

# Exclude markdown (read-only)
python tools/rule_manager.py --enable-rule 50 --sources database config json_export hooks
```

## 🔧 **Error Handling**

### **Missing Sources**
- Gracefully handles missing configuration files
- Provides warnings for unavailable sources
- Continues operation with available sources

### **Database Issues**
- Handles database connection errors
- Provides fallback for missing rules
- Logs warnings for debugging

### **Hook Configuration**
- Handles missing hook configuration
- Provides default behavior for unavailable hooks
- Graceful degradation when hook manager unavailable

## 📊 **Performance Considerations**

### **Efficient Source Checking**
- Parallel source verification where possible
- Cached results for repeated checks
- Optimized database queries

### **Bulk Operations**
- Batch processing for large rule sets
- Progress reporting for long operations
- Memory-efficient processing

## 🧪 **Testing**

### **Unit Tests**
```bash
# Test individual rule status
python tools/rule_manager.py --status-rule 150

# Test sync functionality
python tools/rule_manager.py --sync-all

# Test selective source updates
python tools/rule_manager.py --enable-rule 150 --sources hooks
```

### **Integration Tests**
```bash
# Test full workflow
python tools/rule_manager.py --disable-rule 150 --reason "Test"
python tools/rule_manager.py --status-rule 150
python tools/rule_manager.py --enable-rule 150 --reason "Test complete"
python tools/rule_manager.py --sync-all
```

## 🔍 **Troubleshooting**

### **Common Issues**

#### **Database Connection Errors**
```
Warning: Could not check database for rule 150: Database connection failed
```
**Solution**: Check database configuration and ensure proper API methods are available. The rule manager now uses `get_rule_by_number()` method for database lookups.

#### **Hook Configuration Missing**
```
Warning: Could not get hook status for rule 150: Hook manager not available
```
**Solution**: Ensure hook configuration file exists and hook manager is properly initialized.

#### **Inconsistent Sources**
```
Rule 150: Consistent: No
```
**Solution**: Run `python tools/rule_manager.py --sync-all` to fix inconsistencies.

### **Debug Commands**
```bash
# Check specific rule status
python tools/rule_manager.py --status-rule 150

# Check all rule statuses
python tools/rule_manager.py --status

# Force sync all sources
python tools/rule_manager.py --sync-all
```

## 📈 **Benefits**

### **1. Complete Coverage**
- All rule storage and enforcement mechanisms synchronized across 5 sources
- No more manual synchronization between systems
- Unified rule management across all sources including pre-implementation hooks
- Fixed boolean type consistency issues (0/1 → False/True)

### **2. Intelligent Resolution**
- Automatic conflict detection and resolution
- Majority vote with priority fallback
- Detailed reporting of all changes

### **3. Flexible Control**
- Selective source updates
- Bulk operations for efficiency
- Context-aware rule management

### **4. Robust Error Handling**
- Graceful degradation for missing sources
- Comprehensive error reporting
- Fallback mechanisms for unavailable components

## 🎯 **Future Enhancements**

### **Planned Features**
- Real-time consistency monitoring
- Automated conflict resolution policies
- Enhanced reporting and analytics
- Integration with CI/CD pipelines

### **Potential Improvements**
- Web-based dashboard for rule management
- API endpoints for external integration
- Advanced conflict resolution strategies
- Performance optimization for large rule sets

---

## 📚 **Related Documentation**

- [Hook Management Guide](Hook_Management_Guide.md)
- [Rule Manager Commands](Rule_Manager_Commands.md)
- [Pre-Implementation Hooks Summary](../architecture/COMPREHENSIVE_PRE_IMPLEMENTATION_HOOKS_SUMMARY.md)
- [Master Constitution](../architecture/ZeroUI2.0_Master_Constitution.md)

---

*This enhanced rule consistency verification system provides a robust, intelligent, and comprehensive solution for managing rules across all 5 sources in the ZeroUI 2.0 constitution system.*
