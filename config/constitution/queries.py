#!/usr/bin/env python3
"""
Constitution Rules Database Queries for ZeroUI 2.0

This module provides common database queries for retrieving and filtering
constitution rules with various criteria.
"""

from typing import Dict, List, Optional, Any, Tuple
from .database import ConstitutionRulesDB

class ConstitutionQueries:
    """
    Common database queries for constitution rules.
    
    Provides a high-level interface for common rule queries and operations.
    """
    
    def __init__(self, db_manager: ConstitutionRulesDB):
        """
        Initialize queries with database manager.
        
        Args:
            db_manager: ConstitutionRulesDB instance
        """
        self.db = db_manager
    
    def get_rules_by_priority(self, priority: str, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """
        Get rules by priority level.
        
        Args:
            priority: Priority level (critical, important, recommended)
            enabled_only: If True, return only enabled rules
            
        Returns:
            List of rule dictionaries
        """
        cursor = self.db.connection.cursor()
        
        if enabled_only:
            query = """
                SELECT r.*, rc.enabled, rc.config_data, rc.disabled_reason, rc.disabled_at
                FROM constitution_rules r
                JOIN rule_configuration rc ON r.rule_number = rc.rule_number
                WHERE r.priority = ? AND rc.enabled = 1
                ORDER BY r.rule_number
            """
        else:
            query = """
                SELECT r.*, rc.enabled, rc.config_data, rc.disabled_reason, rc.disabled_at
                FROM constitution_rules r
                JOIN rule_configuration rc ON r.rule_number = rc.rule_number
                WHERE r.priority = ?
                ORDER BY r.rule_number
            """
        
        cursor.execute(query, (priority,))
        rows = cursor.fetchall()
        
        rules = []
        for row in rows:
            rule = dict(row)
            rule['json_metadata'] = self.db._parse_json(rule['json_metadata'])
            rule['config_data'] = self.db._parse_json(rule['config_data']) if rule['config_data'] else {}
            rules.append(rule)
        
        return rules
    
    def search_rules(self, search_term: str, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """
        Search rules by title or content.
        
        Args:
            search_term: Search term to look for
            enabled_only: If True, return only enabled rules
            
        Returns:
            List of matching rule dictionaries
        """
        cursor = self.db.connection.cursor()
        
        search_pattern = f"%{search_term}%"
        
        if enabled_only:
            query = """
                SELECT r.*, rc.enabled, rc.config_data, rc.disabled_reason, rc.disabled_at
                FROM constitution_rules r
                JOIN rule_configuration rc ON r.rule_number = rc.rule_number
                WHERE (r.title LIKE ? OR r.content LIKE ?) AND rc.enabled = 1
                ORDER BY r.rule_number
            """
        else:
            query = """
                SELECT r.*, rc.enabled, rc.config_data, rc.disabled_reason, rc.disabled_at
                FROM constitution_rules r
                JOIN rule_configuration rc ON r.rule_number = rc.rule_number
                WHERE r.title LIKE ? OR r.content LIKE ?
                ORDER BY r.rule_number
            """
        
        cursor.execute(query, (search_pattern, search_pattern))
        rows = cursor.fetchall()
        
        rules = []
        for row in rows:
            rule = dict(row)
            rule['json_metadata'] = self.db._parse_json(rule['json_metadata'])
            rule['config_data'] = self.db._parse_json(rule['config_data']) if rule['config_data'] else {}
            rules.append(rule)
        
        return rules
    
    def get_rules_in_range(self, start_rule: int, end_rule: int, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """
        Get rules within a specific range.
        
        Args:
            start_rule: Starting rule number
            end_rule: Ending rule number
            enabled_only: If True, return only enabled rules
            
        Returns:
            List of rule dictionaries
        """
        cursor = self.db.connection.cursor()
        
        if enabled_only:
            query = """
                SELECT r.*, rc.enabled, rc.config_data, rc.disabled_reason, rc.disabled_at
                FROM constitution_rules r
                JOIN rule_configuration rc ON r.rule_number = rc.rule_number
                WHERE r.rule_number BETWEEN ? AND ? AND rc.enabled = 1
                ORDER BY r.rule_number
            """
        else:
            query = """
                SELECT r.*, rc.enabled, rc.config_data, rc.disabled_reason, rc.disabled_at
                FROM constitution_rules r
                JOIN rule_configuration rc ON r.rule_number = rc.rule_number
                WHERE r.rule_number BETWEEN ? AND ?
                ORDER BY r.rule_number
            """
        
        cursor.execute(query, (start_rule, end_rule))
        rows = cursor.fetchall()
        
        rules = []
        for row in rows:
            rule = dict(row)
            rule['json_metadata'] = self.db._parse_json(rule['json_metadata'])
            rule['config_data'] = self.db._parse_json(rule['config_data']) if rule['config_data'] else {}
            rules.append(rule)
        
        return rules
    
    def get_recently_modified_rules(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recently modified rules.
        
        Args:
            limit: Maximum number of rules to return
            
        Returns:
            List of recently modified rule dictionaries
        """
        cursor = self.db.connection.cursor()
        cursor.execute("""
            SELECT r.*, rc.enabled, rc.config_data, rc.disabled_reason, rc.disabled_at, rc.updated_at
            FROM constitution_rules r
            JOIN rule_configuration rc ON r.rule_number = rc.rule_number
            ORDER BY rc.updated_at DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        
        rules = []
        for row in rows:
            rule = dict(row)
            rule['json_metadata'] = self.db._parse_json(rule['json_metadata'])
            rule['config_data'] = self.db._parse_json(rule['config_data']) if rule['config_data'] else {}
            rules.append(rule)
        
        return rules
    
    def get_rules_by_usage_count(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get rules ordered by usage count.
        
        Args:
            limit: Maximum number of rules to return
            
        Returns:
            List of rule dictionaries with usage counts
        """
        cursor = self.db.connection.cursor()
        cursor.execute("""
            SELECT r.*, rc.enabled, rc.config_data, rc.disabled_reason, rc.disabled_at,
                   COUNT(u.id) as usage_count
            FROM constitution_rules r
            JOIN rule_configuration rc ON r.rule_number = rc.rule_number
            LEFT JOIN rule_usage u ON r.rule_number = u.rule_number
            GROUP BY r.rule_number
            ORDER BY usage_count DESC, r.rule_number
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        
        rules = []
        for row in rows:
            rule = dict(row)
            rule['json_metadata'] = self.db._parse_json(rule['json_metadata'])
            rule['config_data'] = self.db._parse_json(rule['config_data']) if rule['config_data'] else {}
            rules.append(rule)
        
        return rules
    
    def get_validation_summary(self, rule_number: Optional[int] = None) -> Dict[str, Any]:
        """
        Get validation summary for rules.
        
        Args:
            rule_number: Optional specific rule number
            
        Returns:
            Validation summary dictionary
        """
        cursor = self.db.connection.cursor()
        
        if rule_number:
            cursor.execute("""
                SELECT validation_result, COUNT(*) as count
                FROM validation_history
                WHERE rule_number = ?
                GROUP BY validation_result
            """, (rule_number,))
        else:
            cursor.execute("""
                SELECT validation_result, COUNT(*) as count
                FROM validation_history
                GROUP BY validation_result
            """)
        
        rows = cursor.fetchall()
        
        summary = {
            "total_validations": 0,
            "results": {}
        }
        
        for row in rows:
            result, count = row
            summary["results"][result] = count
            summary["total_validations"] += count
        
        return summary
    
    def get_category_statistics(self) -> Dict[str, Dict[str, Any]]:
        """
        Get detailed statistics for each category.
        
        Returns:
            Dictionary with category statistics
        """
        cursor = self.db.connection.cursor()
        cursor.execute("""
            SELECT r.category, 
                   COUNT(*) as total_rules,
                   SUM(CASE WHEN rc.enabled = 1 THEN 1 ELSE 0 END) as enabled_rules,
                   SUM(CASE WHEN rc.enabled = 0 THEN 1 ELSE 0 END) as disabled_rules,
                   r.priority
            FROM constitution_rules r
            JOIN rule_configuration rc ON r.rule_number = rc.rule_number
            GROUP BY r.category, r.priority
            ORDER BY r.category
        """)
        
        rows = cursor.fetchall()
        
        stats = {}
        for row in rows:
            category, total, enabled, disabled, priority = row
            stats[category] = {
                "total_rules": total,
                "enabled_rules": enabled,
                "disabled_rules": disabled,
                "enabled_percentage": (enabled / total * 100) if total > 0 else 0,
                "priority": priority
            }
        
        return stats
    
    def get_rule_dependencies(self, rule_number: int) -> List[Dict[str, Any]]:
        """
        Get rules that might be related or dependent on the given rule.
        
        Args:
            rule_number: Rule number to find dependencies for
            
        Returns:
            List of related rule dictionaries
        """
        # Get the rule first
        rule = self.db.get_rule_by_number(rule_number)
        if not rule:
            return []
        
        # Search for rules in the same category
        same_category_rules = self.db.get_rules_by_category(rule['category'])
        
        # Filter out the rule itself
        related_rules = [r for r in same_category_rules if r['rule_number'] != rule_number]
        
        return related_rules
    
    def get_enterprise_critical_rules(self) -> List[Dict[str, Any]]:
        """
        Get rules that are marked as enterprise critical.
        
        Returns:
            List of enterprise critical rule dictionaries
        """
        # Enterprise critical rules are typically those in critical categories
        critical_categories = ["basic_work", "system_design", "problem_solving", 
                              "platform", "teamwork", "code_review", "coding_standards"]
        
        all_critical_rules = []
        for category in critical_categories:
            rules = self.db.get_rules_by_category(category, enabled_only=True)
            all_critical_rules.extend(rules)
        
        # Sort by rule number
        all_critical_rules.sort(key=lambda x: x['rule_number'])
        
        return all_critical_rules
    
    def get_rule_usage_history(self, rule_number: int, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get usage history for a specific rule.
        
        Args:
            rule_number: Rule number
            limit: Maximum number of history entries
            
        Returns:
            List of usage history entries
        """
        cursor = self.db.connection.cursor()
        cursor.execute("""
            SELECT action, context, timestamp
            FROM rule_usage
            WHERE rule_number = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (rule_number, limit))
        
        rows = cursor.fetchall()
        
        history = []
        for row in rows:
            history.append(dict(row))
        
        return history
    
    def get_validation_history(self, rule_number: int, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get validation history for a specific rule.
        
        Args:
            rule_number: Rule number
            limit: Maximum number of history entries
            
        Returns:
            List of validation history entries
        """
        cursor = self.db.connection.cursor()
        cursor.execute("""
            SELECT validation_result, details, timestamp
            FROM validation_history
            WHERE rule_number = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (rule_number, limit))
        
        rows = cursor.fetchall()
        
        history = []
        for row in rows:
            history.append(dict(row))
        
        return history
    
    def get_rule_analytics(self) -> Dict[str, Any]:
        """
        Get comprehensive analytics for all rules.
        
        Returns:
            Analytics dictionary
        """
        cursor = self.db.connection.cursor()
        
        # Basic statistics
        cursor.execute("SELECT COUNT(*) FROM constitution_rules")
        total_rules = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM rule_configuration WHERE enabled = 1")
        enabled_rules = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM rule_configuration WHERE enabled = 0")
        disabled_rules = cursor.fetchone()[0]
        
        # Category breakdown
        category_stats = self.get_category_statistics()
        
        # Usage statistics
        cursor.execute("SELECT COUNT(*) FROM rule_usage")
        total_usage_events = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM validation_history")
        total_validations = cursor.fetchone()[0]
        
        # Most used rules
        most_used = self.get_rules_by_usage_count(5)
        
        # Recently modified
        recently_modified = self.get_recently_modified_rules(5)
        
        return {
            "total_rules": total_rules,
            "enabled_rules": enabled_rules,
            "disabled_rules": disabled_rules,
            "enabled_percentage": (enabled_rules / total_rules * 100) if total_rules > 0 else 0,
            "category_statistics": category_stats,
            "total_usage_events": total_usage_events,
            "total_validations": total_validations,
            "most_used_rules": most_used,
            "recently_modified_rules": recently_modified
        }


# Helper function to create queries instance
def create_queries(db_path: str = "config/constitution_rules.db") -> ConstitutionQueries:
    """
    Create a ConstitutionQueries instance.
    
    Args:
        db_path: Path to SQLite database file
        
    Returns:
        ConstitutionQueries instance
    """
    db_manager = ConstitutionRulesDB(db_path)
    return ConstitutionQueries(db_manager)


# Example usage
def main():
    """Example usage of the Constitution Queries."""
    
    with ConstitutionRulesDB() as db:
        queries = ConstitutionQueries(db)
        
        print("Constitution Rules Queries initialized")
        
        # Get analytics
        analytics = queries.get_rule_analytics()
        print(f"\nAnalytics:")
        print(f"Total rules: {analytics['total_rules']}")
        print(f"Enabled: {analytics['enabled_rules']} ({analytics['enabled_percentage']:.1f}%)")
        print(f"Disabled: {analytics['disabled_rules']}")
        
        # Get category statistics
        category_stats = queries.get_category_statistics()
        print(f"\nCategory Statistics:")
        for category, stats in category_stats.items():
            print(f"  {category}: {stats['enabled_rules']}/{stats['total_rules']} enabled ({stats['enabled_percentage']:.1f}%)")
        
        # Search for rules
        search_results = queries.search_rules("security", enabled_only=True)
        print(f"\nSecurity-related rules: {len(search_results)}")
        for rule in search_results[:3]:
            print(f"  Rule {rule['rule_number']}: {rule['title']}")
        
        # Get enterprise critical rules
        critical_rules = queries.get_enterprise_critical_rules()
        print(f"\nEnterprise critical rules: {len(critical_rules)}")
        
        # Get most used rules
        most_used = queries.get_rules_by_usage_count(5)
        print(f"\nMost used rules:")
        for rule in most_used:
            print(f"  Rule {rule['rule_number']}: {rule['title']} (used {rule.get('usage_count', 0)} times)")


if __name__ == "__main__":
    main()
