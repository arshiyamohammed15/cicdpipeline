# Single Source of Truth: Rule Management System

## Problem Statement

Previously, constitution rules existed in **5 places**:
1. **Markdown** - `ZeroUI2.0_Master_Constitution.md`
2. **SQLite Database** - `config/constitution_rules.db`
3. **JSON Export** - `config/constitution_rules.json`
4. **Config** - `config/constitution_config.json`
5. **Hooks** - `config/hook_config.json`

**Issue**: Adding, removing, or updating a rule required manual changes in all 5 locations, creating:
- Complex inconsistencies
- Manual synchronization overhead
- Risk of conflicting data
- Difficult maintenance

## Solution: Single Source of Truth Architecture

### New Architecture

```
┌────────────────────────────────────────────────────┐
│   MARKDOWN (Single Source of Truth)                │
│   ZeroUI2.0_Master_Constitution.md                 │
│   • ALL rule definitions                           │
│   • Titles, content, categories                    │
│   • Version controlled in Git                      │
│   • The ONLY file you edit                         │
└──────────────────┬─────────────────────────────────┘
                   │
                   │ ONE-WAY REBUILD →
                   │
      ┌────────────┴────────────┐
      │                         │
      ↓                         ↓
┌─────────────┐         ┌──────────────┐
│   SQLite    │         │    JSON      │
│  Database   │         │   Export     │
│  (Cache)    │         │   (Cache)    │
│  Read-Only  │         │  Read-Only   │
└─────────────┘         └──────────────┘
      │                         │
      │   Runtime Queries       │
      │   (Fast Access)         │
      │                         │
      └────────────┬────────────┘
                   │
                   │ Lookup Only ↓
                   │
      ┌────────────▼─────────────┐
      │     CONFIG (State Only)  │
      │  constitution_config.json│
      │  • enabled: true/false   │
      │  • disabled_reason       │
      │  • disabled_at           │
      │  NO rule content here!   │
      └──────────────────────────┘
      │
      │ HOOKS (Pre-Implementation)
      │ hook_config.json
      │ • enabled: true/false
      │ • category mappings
      │ • enforcement rules
      └──────────────────────────┘
```

### Key Concepts

1. **Markdown = Source**: All rule content lives ONLY in Markdown
2. **DB/JSON = Caches**: Auto-generated from Markdown, never edited directly
3. **Config = State**: Only stores enabled/disabled flags, no content
4. **Hooks = Enforcement**: Pre-implementation rule enforcement, synchronized with state
5. **One-Way Flow**: Markdown → DB/JSON (rebuild), never the reverse

## Workflow: How to Modify Rules

### Adding a New Rule

```bash
# 1. Edit Markdown (ONLY place to edit)
vim ZeroUI2.0_Master_Constitution.md

# Add:
# **Rule 219: New Security Rule**
# Never store passwords in plain text.

# 2. Rebuild derived artifacts
python enhanced_cli.py --rebuild-from-markdown

# Output:
# ✓ Found 219 rules in Markdown
# ✓ Rebuilt SQLite database with 219 rules
# ✓ Rebuilt JSON database with 219 rules
# ✓ All sources are consistent

# 3. Verify consistency
python enhanced_cli.py --verify-consistency

# 4. Commit to Git (only Markdown tracked)
git add ZeroUI2.0_Master_Constitution.md
git commit -m "Add Rule 219: New Security Rule"
```

### Updating an Existing Rule

```bash
# 1. Edit Markdown
vim ZeroUI2.0_Master_Constitution.md

# Change Rule 150 content

# 2. Rebuild
python enhanced_cli.py --rebuild-from-markdown

# 3. Commit
git add ZeroUI2.0_Master_Constitution.md
git commit -m "Update Rule 150: Enhanced input validation guidance"
```

### Removing a Rule

```bash
# 1. Remove from Markdown
vim ZeroUI2.0_Master_Constitution.md

# Delete Rule 150 section

# 2. Rebuild (will remove from DB/JSON automatically)
python enhanced_cli.py --rebuild-from-markdown

# 3. Commit
git add ZeroUI2.0_Master_Constitution.md
git commit -m "Remove Rule 150: Deprecated"
```

### Enabling/Disabling Rules (Runtime State)

```bash
# These commands only affect Config (state), not content

# Disable a rule
python enhanced_cli.py --disable-rule 150 --disable-reason "Too restrictive for current project"

# Enable a rule
python enhanced_cli.py --enable-rule 150

# State persists across rebuilds
```

## Rebuild Process Details

What happens when you run `--rebuild-from-markdown`:

1. **Extract [1/6]**: Parse all rules from Markdown
2. **Preserve [2/6]**: Save current enabled/disabled states from Config
3. **Rebuild SQLite [3/6]**: Clear database, insert all rules from Markdown
4. **Rebuild JSON [4/6]**: Regenerate JSON with all rules from Markdown
5. **Update Config [5/6]**: Clean Config to only contain state (no content)
6. **Verify [6/6]**: Validate consistency across all sources

**Preserved Across Rebuilds**:
- Enabled/disabled states
- Disabled reasons
- Disabled timestamps

**Regenerated from Markdown**:
- Rule numbers
- Titles
- Content
- Categories
- Priorities

## Benefits

| Benefit | Description |
|---------|-------------|
| **Single Edit Point** | Edit rules only in Markdown |
| **No Sync Conflicts** | DB/JSON are regenerated, not synced |
| **Version Control** | All changes tracked in Git (Markdown) |
| **Easy PR Reviews** | PRs show clear Markdown diffs |
| **Fast Runtime** | DB/JSON still available for performance |
| **Separation of Concerns** | Content (Markdown) vs State (Config) |
| **Can't Get Out of Sync** | Rebuild ensures consistency |
| **Automatic Backup** | JSON serves as automatic backup |

## Commands Reference

```bash
# Rebuild from Markdown (after editing rules)
python enhanced_cli.py --rebuild-from-markdown

# Verify all sources are consistent
python enhanced_cli.py --verify-consistency

# View rule statistics
python enhanced_cli.py --rule-stats

# List all rules
python enhanced_cli.py --list-rules

# Enable/disable rules (state only)
python enhanced_cli.py --enable-rule 150
python enhanced_cli.py --disable-rule 150 --disable-reason "Testing"

# Search rules
python enhanced_cli.py --search-rules "exception handling"

# Export rules
python enhanced_cli.py --export-rules --format json
```

## Migration Notes

### For Existing Systems

If you have an existing system with rules in multiple locations:

1. **Verify current state**:
   ```bash
   python enhanced_cli.py --verify-consistency
   ```

2. **If inconsistent**, choose your source of truth:
   - **Option A**: Markdown is correct → Just rebuild
   - **Option B**: Database is correct → Export to Markdown first
   - **Option C**: Merge conflicts → Manual resolution needed

3. **Rebuild once** to establish the new pattern:
   ```bash
   python enhanced_cli.py --rebuild-from-markdown
   ```

4. **From now on**: Only edit Markdown, then rebuild

### Backward Compatibility

- Config format remains compatible (v2.0)
- Existing enabled/disabled states are preserved
- Database schema unchanged
- JSON export format unchanged
- All existing commands continue to work

## Implementation Details

### Files Modified

1. **enhanced_cli.py**:
   - Added `--rebuild-from-markdown` command
   - Added `_rebuild_from_markdown()` method

2. **README.md**:
   - Documented Single Source of Truth architecture
   - Added workflow examples

3. **SINGLE_SOURCE_OF_TRUTH.md** (this file):
   - Complete system documentation

### Files NOT Modified

- Database schema (unchanged)
- JSON export format (unchanged)
- Rule extraction logic (unchanged)
- Validation logic (unchanged)

## FAQ

**Q: Can I still edit rules in the database?**  
A: Technically yes, but changes will be lost on next rebuild. Always edit Markdown instead.

**Q: What happens to my enabled/disabled states?**  
A: They are preserved in Config and restored after rebuild.

**Q: Can I still use the JSON export?**  
A: Yes, but it's auto-generated from Markdown. Don't edit it directly.

**Q: How do I revert a rule change?**  
A: Use Git to revert the Markdown, then rebuild.

**Q: What if Markdown gets corrupted?**  
A: Restore from Git history. JSON serves as a backup too.

**Q: Do I need to rebuild after every edit?**  
A: Yes, but it's fast (~2 seconds) and ensures consistency.

**Q: Can I automate the rebuild?**  
A: Yes, add a Git pre-commit hook or CI/CD step.

## Success Metrics

✅ **All 218 rules** extracted from Markdown  
✅ **SQLite database** rebuilt successfully  
✅ **JSON export** regenerated successfully  
✅ **Config** cleaned to state-only  
✅ **All sources** verified consistent  
✅ **Enabled/disabled states** preserved  
✅ **Rebuild time** < 2 seconds  

## Future Enhancements

1. **Git Pre-Commit Hook**: Auto-rebuild on Markdown changes
2. **CI/CD Validation**: Ensure consistency in PRs
3. **Read-Only Enforcement**: Add checks to prevent DB/JSON edits
4. **Backup Rotation**: Automatic Markdown backups before rebuild
5. **Diff Reporting**: Show what changed after rebuild

---

**Last Updated**: 2025-10-20  
**Version**: 1.0  
**Status**: Production Ready

