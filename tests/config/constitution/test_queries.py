from __future__ import annotations

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from config.constitution import queries


class FakeDB:
    """Fake database for testing queries."""
    
    def __init__(self):
        self.rules = [
            {
                "rule_number": 1,
                "title": "Security Rule",
                "category": "basic_work",
                "priority": "critical",
                "content": "Security content",
                "enabled": True,
                "json_metadata": '{"usage_count": 5}',
                "config_data": '{"threshold": 10}'
            },
            {
                "rule_number": 2,
                "title": "Performance Rule",
                "category": "performance",
                "priority": "important",
                "content": "Performance content",
                "enabled": True,
                "json_metadata": '{"usage_count": 3}',
                "config_data": '{}'
            },
            {
                "rule_number": 3,
                "title": "Code Quality",
                "category": "quality",
                "priority": "recommended",
                "content": "Quality content",
                "enabled": False,
                "json_metadata": '{"usage_count": 1}',
                "config_data": '{}'
            }
        ]
        self.usage_history = [
            {"action": "enabled", "context": "test", "timestamp": "2024-01-01T00:00:00"},
            {"action": "used", "context": "validation", "timestamp": "2024-01-02T00:00:00"}
        ]
        self.validation_history = [
            {"validation_result": "passed", "details": "OK", "timestamp": "2024-01-01T00:00:00"},
            {"validation_result": "failed", "details": "Error", "timestamp": "2024-01-02T00:00:00"}
        ]
        self._parse_json_called = []
        
    def _parse_json(self, json_str):
        """Parse JSON string."""
        self._parse_json_called.append(json_str)
        import json
        if json_str:
            return json.loads(json_str)
        return {}
    
    @property
    def connection(self):
        """Fake connection."""
        return self
    
    def cursor(self):
        """Fake cursor."""
        return FakeCursor(self)


class FakeCursor:
    """Fake database cursor."""
    
    def __init__(self, db):
        self.db = db
        self._results = []
        self._query = None
        self._params = None
        
    def execute(self, query, params=None):
        """Execute query."""
        self._query = query
        self._params = params
        
        # Simulate query results based on query
        # Check for category statistics query first (most specific)
        if "JOIN rule_configuration" in query and "GROUP BY" in query and "category" in query:
            # Category statistics query - return tuples: (category, total_rules, enabled_rules, disabled_rules, priority)
            self._results = [
                ("basic_work", 1, 1, 0, "critical"),
                ("performance", 1, 1, 0, "important")
            ]
        elif "priority" in query:
            priority = params[0] if params else None
            self._results = [self._row_to_dict(r) for r in self.db.rules 
                           if r["priority"] == priority]
        elif "LIKE" in query:
            search_term = params[0].replace("%", "") if params else ""
            self._results = [self._row_to_dict(r) for r in self.db.rules
                           if search_term.lower() in r["title"].lower() or 
                              search_term.lower() in r["content"].lower()]
        elif "BETWEEN" in query:
            start, end = params if params else (1, 100)
            self._results = [self._row_to_dict(r) for r in self.db.rules
                           if start <= r["rule_number"] <= end]
        elif "ORDER BY rc.updated_at DESC" in query:
            self._results = [self._row_to_dict(r) for r in self.db.rules]
        elif "usage_count" in query:
            self._results = [self._row_to_dict(r) for r in self.db.rules]
            for r in self._results:
                r["usage_count"] = self.db.rules[r["rule_number"] - 1].get("json_metadata", {}).get("usage_count", 0) if isinstance(self.db.rules[r["rule_number"] - 1].get("json_metadata"), dict) else 0
        elif "validation_result" in query and "COUNT" in query:
            # Return tuples for SQLite-style results: (validation_result, count)
            self._results = [
                ("passed", 1),
                ("failed", 1)
            ]
        elif "JOIN rule_configuration" in query and "GROUP BY" in query:
            # Category statistics query - return tuples: (category, total_rules, enabled_rules, disabled_rules, priority)
            self._results = [
                ("basic_work", 1, 1, 0, "critical"),
                ("performance", 1, 1, 0, "important")
            ]
        elif "SELECT r.category" in query or ("category" in query and "GROUP BY" in query and "JOIN" in query):
            # Return tuples for SQLite-style results: (category, total_rules, enabled_rules, disabled_rules, priority)
            self._results = [
                ("basic_work", 1, 1, 0, "critical"),
                ("performance", 1, 1, 0, "important")
            ]
        elif "COUNT" in query and "constitution_rules" in query:
            # Return tuple for SQLite-style COUNT query: (count,)
            self._results = [(len(self.db.rules),)]
        elif "COUNT" in query and "rule_configuration" in query:
            enabled = sum(1 for r in self.db.rules if r["enabled"])
            # Return tuple for SQLite-style COUNT query: (count,)
            self._results = [(enabled,)]
        elif "rule_usage" in query and "COUNT" in query:
            # Return tuple for SQLite-style COUNT query: (count,)
            self._results = [(len(self.db.usage_history),)]
        elif "validation_history" in query and "COUNT" in query:
            # Return tuple for SQLite-style COUNT query: (count,)
            self._results = [(len(self.db.validation_history),)]
        else:
            self._results = [self._row_to_dict(r) for r in self.db.rules]
            
        # Apply enabled_only filter if present
        if params and len(params) > 0 and "enabled = 1" in query:
            self._results = [r for r in self._results if r.get("enabled", True)]
            
    def fetchall(self):
        """Fetch all results."""
        # If _results contains tuples (for COUNT queries), return them directly
        if self._results and isinstance(self._results[0], tuple):
            return self._results
        # Otherwise wrap in FakeRow
        return [FakeRow(r) for r in self._results]
    
    def fetchone(self):
        """Fetch one result."""
        if self._results:
            # If result is a tuple (for COUNT queries), return it directly
            if isinstance(self._results[0], tuple):
                return self._results[0]
            return FakeRow(self._results[0])
        return None
    
    def _row_to_dict(self, rule):
        """Convert rule to dict format."""
        return {
            "rule_number": rule["rule_number"],
            "title": rule["title"],
            "category": rule["category"],
            "priority": rule["priority"],
            "content": rule["content"],
            "enabled": rule["enabled"],
            "json_metadata": rule["json_metadata"],
            "config_data": rule["config_data"]
        }


class FakeRow:
    """Fake database row."""
    
    def __init__(self, data):
        self._data = data
        
    def __getitem__(self, key):
        # Support both dict-style, tuple-style, and numeric index access on dicts
        if isinstance(self._data, tuple):
            return self._data[key]
        if isinstance(key, int):
            return list(self._data.values())[key]
        return self._data[key]
    
    def keys(self):
        if isinstance(self._data, tuple):
            return range(len(self._data))
        return self._data.keys()
    
    def __iter__(self):
        if isinstance(self._data, tuple):
            return iter(self._data)
        return iter(self._data.items())


@pytest.fixture
def fake_db():
    """Create fake database."""
    return FakeDB()


@pytest.fixture
def db_manager(fake_db):
    """Create database manager with fake DB."""
    manager = Mock()
    manager.connection = fake_db
    manager._parse_json = fake_db._parse_json
    return manager


@pytest.fixture
def queries_instance(db_manager):
    """Create queries instance."""
    return queries.ConstitutionQueries(db_manager)


@pytest.mark.constitution
def test_get_rules_by_priority(queries_instance):
    """Test getting rules by priority."""
    results = queries_instance.get_rules_by_priority("critical")
    assert len(results) == 1
    assert results[0]["priority"] == "critical"


@pytest.mark.constitution
def test_get_rules_by_priority_enabled_only(queries_instance):
    """Test getting enabled rules by priority."""
    results = queries_instance.get_rules_by_priority("critical", enabled_only=True)
    assert len(results) == 1
    assert all(r["enabled"] for r in results)


@pytest.mark.constitution
def test_search_rules(queries_instance):
    """Test searching rules."""
    results = queries_instance.search_rules("Security")
    assert len(results) == 1
    assert "Security" in results[0]["title"]


@pytest.mark.constitution
def test_search_rules_enabled_only(queries_instance):
    """Test searching only enabled rules."""
    results = queries_instance.search_rules("Rule", enabled_only=True)
    assert len(results) >= 1
    assert all(r["enabled"] for r in results)


@pytest.mark.constitution
def test_get_rules_in_range(queries_instance):
    """Test getting rules in range."""
    results = queries_instance.get_rules_in_range(1, 2)
    assert len(results) == 2
    assert all(1 <= r["rule_number"] <= 2 for r in results)


@pytest.mark.constitution
def test_get_rules_in_range_enabled_only(queries_instance):
    """Test getting enabled rules in range."""
    results = queries_instance.get_rules_in_range(1, 3, enabled_only=True)
    assert len(results) >= 1
    assert all(r["enabled"] for r in results)


@pytest.mark.constitution
def test_get_recently_modified_rules(queries_instance):
    """Test getting recently modified rules."""
    results = queries_instance.get_recently_modified_rules(limit=5)
    assert len(results) <= 5
    assert isinstance(results, list)


@pytest.mark.constitution
def test_get_rules_by_usage_count(queries_instance):
    """Test getting rules by usage count."""
    results = queries_instance.get_rules_by_usage_count(limit=5)
    assert len(results) <= 5
    assert isinstance(results, list)


@pytest.mark.constitution
def test_get_validation_summary_all_rules(queries_instance):
    """Test getting validation summary for all rules."""
    summary = queries_instance.get_validation_summary()
    assert "total_validations" in summary
    assert "results" in summary


@pytest.mark.constitution
def test_get_validation_summary_specific_rule(queries_instance):
    """Test getting validation summary for specific rule."""
    summary = queries_instance.get_validation_summary(rule_number=1)
    assert "total_validations" in summary
    assert "results" in summary


@pytest.mark.constitution
def test_get_category_statistics(queries_instance):
    """Test getting category statistics."""
    stats = queries_instance.get_category_statistics()
    assert isinstance(stats, dict)
    # Should have category entries
    assert len(stats) > 0


@pytest.mark.constitution
def test_get_rule_dependencies(queries_instance, db_manager):
    """Test getting rule dependencies."""
    # Mock get_rule_by_number and get_rules_by_category
    db_manager.get_rule_by_number.return_value = {
        "rule_number": 1,
        "category": "basic_work"
    }
    db_manager.get_rules_by_category.return_value = [
        {"rule_number": 1, "category": "basic_work"},
        {"rule_number": 4, "category": "basic_work"}
    ]
    
    dependencies = queries_instance.get_rule_dependencies(1)
    assert isinstance(dependencies, list)
    # Should not include the rule itself
    assert all(r["rule_number"] != 1 for r in dependencies)


@pytest.mark.constitution
def test_get_rule_dependencies_not_found(queries_instance, db_manager):
    """Test getting dependencies for non-existent rule."""
    db_manager.get_rule_by_number.return_value = None
    
    dependencies = queries_instance.get_rule_dependencies(999)
    assert dependencies == []


@pytest.mark.constitution
def test_get_enterprise_critical_rules(queries_instance, db_manager):
    """Test getting enterprise critical rules."""
    db_manager.get_rules_by_category.return_value = [
        {"rule_number": 1, "enabled": True, "category": "basic_work"}
    ]
    
    critical_rules = queries_instance.get_enterprise_critical_rules()
    assert isinstance(critical_rules, list)


@pytest.mark.constitution
def test_get_rule_usage_history(queries_instance, fake_db):
    """Test getting rule usage history."""
    # Mock cursor for usage history query
    fake_cursor = Mock()
    fake_cursor.execute.return_value = None
    fake_cursor.fetchall.return_value = [
        FakeRow(h) for h in fake_db.usage_history
    ]
    
    with patch.object(queries_instance.db.connection, 'cursor', return_value=fake_cursor):
        history = queries_instance.get_rule_usage_history(1, limit=20)
        assert isinstance(history, list)
        assert len(history) == 2


@pytest.mark.constitution
def test_get_validation_history(queries_instance, fake_db):
    """Test getting validation history."""
    # Mock cursor for validation history query
    fake_cursor = Mock()
    fake_cursor.execute.return_value = None
    fake_cursor.fetchall.return_value = [
        FakeRow(h) for h in fake_db.validation_history
    ]
    
    with patch.object(queries_instance.db.connection, 'cursor', return_value=fake_cursor):
        history = queries_instance.get_validation_history(1, limit=20)
        assert isinstance(history, list)
        assert len(history) == 2


@pytest.mark.constitution
def test_get_rule_analytics(queries_instance, fake_db):
    """Test getting comprehensive rule analytics."""
    # Mock cursor for analytics queries
    fake_cursor = Mock()
    
    def mock_execute(query, params=None):
        if "COUNT" in query and "constitution_rules" in query:
            fake_cursor.fetchone.return_value = FakeRow({"count": 3})
        elif "COUNT" in query and "rule_configuration" in query and "enabled = 1" in query:
            fake_cursor.fetchone.return_value = FakeRow({"count": 2})
        elif "COUNT" in query and "rule_configuration" in query and "enabled = 0" in query:
            fake_cursor.fetchone.return_value = FakeRow({"count": 1})
        elif "rule_usage" in query:
            fake_cursor.fetchone.return_value = FakeRow({"count": 5})
        elif "validation_history" in query:
            fake_cursor.fetchone.return_value = FakeRow({"count": 3})
    
    fake_cursor.execute = mock_execute
    
    with patch.object(queries_instance.db.connection, 'cursor', return_value=fake_cursor):
        with patch.object(queries_instance, 'get_category_statistics', return_value={}):
            with patch.object(queries_instance, 'get_rules_by_usage_count', return_value=[]):
                with patch.object(queries_instance, 'get_recently_modified_rules', return_value=[]):
                    analytics = queries_instance.get_rule_analytics()
                    
                    assert "total_rules" in analytics
                    assert "enabled_rules" in analytics
                    assert "disabled_rules" in analytics
                    assert "enabled_percentage" in analytics
                    assert "category_statistics" in analytics
                    assert "total_usage_events" in analytics
                    assert "total_validations" in analytics


@pytest.mark.constitution
def test_create_queries(tmp_path):
    """Test creating queries instance."""
    with patch('config.constitution.queries.ConstitutionRulesDB') as mock_db_class:
        mock_db = Mock()
        mock_db_class.return_value = mock_db
        
        queries_instance = queries.create_queries(str(tmp_path / "test.db"))
        assert isinstance(queries_instance, queries.ConstitutionQueries)
        assert queries_instance.db == mock_db

