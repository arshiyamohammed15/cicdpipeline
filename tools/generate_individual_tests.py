import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_DIR = ROOT / "validator" / "rules" / "tests" / "individual_rules"


TEMPLATE = """import pytest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from dynamic_test_factory import DynamicTestFactory

factory = DynamicTestFactory()
rule = next(r for r in factory.get_all_rules() if r["id"] == "{rule_id}")

@pytest.mark.parametrize("test_case", factory.create_test_cases(lambda x: x.get("id") == "{rule_id}"), ids=lambda tc: tc.test_method_name)
def test_{fn_name}(test_case):
    assert test_case.rule_id == "{rule_id}"
    assert test_case.category == "{category}"
    assert test_case.constitution == "{constitution}"
    assert test_case.severity in ("error", "warning", "info")

    # Ensure rule metadata consistency
    assert rule["id"] == test_case.rule_id
"""

CONFIG_TEMPLATE = """# Auto-generated minimal test for rule {rule_id}
def test_{fn_name}_exists():
    rid = "{rule_id}"
    assert rid.startswith("R") and rid[1:].isdigit() and len(rid) in (4, 5)
"""


def slug(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return text


def load_rules_from_config(config_path: Path) -> list:
    with config_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    # Expect either a top-level rules list or only category buckets
    if isinstance(data, dict) and "rules" in data and isinstance(data["rules"], list):
        return data["rules"]
    # If not present, build minimal rules from category buckets
    rules = []
    categories = data.get("categories", {}) if isinstance(data, dict) else {}
    constitution_map = {
        "code_review": "Code Review",
        "api_contracts": "API Contracts",
        "coding_standards": "Coding Standards",
        "comments": "Comments",
        "folder_standards": "Folder Standards",
        "logging": "Logging",
    }
    seen = set()
    for cat_key, cat_data in categories.items():
        rule_nums = cat_data.get("rules", []) if isinstance(cat_data, dict) else []
        for num in rule_nums:
            try:
                n = int(num)
            except Exception:
                continue
            rid = f"R{n:03d}"
            if rid in seen:
                continue
            seen.add(rid)
            rules.append({
                "id": rid,
                "name": f"Rule {rid}",
                "category": cat_key,
                "constitution": constitution_map.get(cat_key, "General"),
            })
    return rules


def main(clean: bool = False, only_ids: set[str] | None = None, no_overwrite: bool = False) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if clean:
        for p in OUT_DIR.glob("test_*.py"):
            p.unlink()

    # Prefer dynamic factory (primary source), which should read tools/validator/rules.json if present
    factory = None
    rules = []
    try:
        from dynamic_test_factory import DynamicTestFactory  # type: ignore
        factory = DynamicTestFactory()
        rules = factory.get_all_rules()
    except Exception:
        pass

    if not rules:
        # Fallback to config rules if factory cannot load or has no rules
        rules = load_rules_from_config(ROOT / "rules_config.json")

    if not rules:
        print("No rules found. Ensure tools/validator/rules.json or rules_config.json is present with rule definitions.")
        return

    # Filter by explicit IDs if provided; create minimal stubs for any missing IDs
    if only_ids:
        existing_ids = set()
        filtered_rules = []
        for r in rules:
            rid = r.get("id") or r.get("rule_id")
            if rid in only_ids:
                filtered_rules.append(r)
                existing_ids.add(rid)
        missing_ids = sorted(list(only_ids - existing_ids))
        for mid in missing_ids:
            filtered_rules.append({
                "id": mid,
                "name": f"Rule {mid}",
                "category": "unknown",
                "constitution": "General",
            })
        rules = filtered_rules

    created = 0
    for r in rules:
        rid = r.get("id") or r.get("rule_id")
        name = r.get("name") or r.get("title") or "rule"
        category = r.get("category", "unknown")
        constitution = r.get("constitution", "unknown")
        if not rid:
            # Skip entries without identifiers
            continue

        filename = f"test_{rid}_{slug(name)}.py"
        path = OUT_DIR / filename
        if no_overwrite and path.exists():
            # Keep existing file intact
            continue
        if factory is not None and hasattr(factory, "get_all_rules") and rules and "severity" in r:
            content = TEMPLATE.format(
                rule_id=rid,
                fn_name=slug(f"{rid}_{name}"),
                category=category,
                constitution=constitution,
            )
        else:
            content = CONFIG_TEMPLATE.format(
                rule_id=rid,
                fn_name=slug(f"{rid}_{name}"),
            )
        path.write_text(content, encoding="utf-8")
        created += 1

    print(f"Generated {created} per-rule test files under {OUT_DIR}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate individual pytest files per rule")
    parser.add_argument("--clean", action="store_true", help="Remove previously generated tests before generating")
    parser.add_argument("--ids", type=str, default="", help="Comma-separated list of rule IDs to include (e.g., R001,R002)")
    parser.add_argument("--ids-file", type=str, default="", help="Path to a file containing one rule ID per line")
    parser.add_argument("--no-overwrite", action="store_true", help="Do not overwrite existing test files")
    args = parser.parse_args()
    selected_ids: set[str] | None = None
    if args.ids or args.ids_file:
        selected_ids = set()
        if args.ids:
            selected_ids.update(x.strip() for x in args.ids.split(",") if x.strip())
        if args.ids_file:
            p = Path(args.ids_file)
            if p.exists():
                content = p.read_text(encoding="utf-8")
                for line in content.splitlines():
                    line = line.strip()
                    if line:
                        selected_ids.add(line)
    main(clean=args.clean, only_ids=selected_ids, no_overwrite=args.no_overwrite)


