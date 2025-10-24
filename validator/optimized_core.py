#!/usr/bin/env python3
"""
Optimized core validation engine for ZEROUI 2.0 Constitution rules.

This module provides high-performance validation with AST caching, parallel processing,
and optimized rule execution.
"""

import ast
import logging
import json
import re
import os
import time
import hashlib
from typing import Dict, List, Tuple, Any, Optional, Set
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache

from .models import Violation, ValidationResult, Severity
from .analyzer import CodeAnalyzer
from .reporter import ReportGenerator

# Import enhanced configuration manager
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.enhanced_config_manager import EnhancedConfigManager


class OptimizedConstitutionValidator:
    """
    High-performance validator with caching and parallel processing.
    
    This validator implements:
    - AST caching for repeated file analysis
    - Parallel rule processing
    - Optimized configuration loading
    - Memory-efficient violation tracking
    """
    
    def __init__(self, config_dir: str = "config"):
        """
        Initialize the optimized validator.
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = config_dir
        self.config_manager = EnhancedConfigManager(config_dir)
        self.analyzer = CodeAnalyzer()
        self.reporter = ReportGenerator()
        
        # Performance optimization caches
        self._ast_cache: Dict[str, Tuple[ast.AST, float]] = {}
        self._file_hash_cache: Dict[str, str] = {}
        self._rule_cache: Dict[str, Any] = {}
        self._pattern_cache: Dict[str, Any] = {}
        
        # Performance metrics
        self._metrics = {
            "files_processed": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_processing_time": 0.0,
            "ast_parsing_time": 0.0,
            "rule_processing_time": 0.0
        }
        
        # Initialize rule processors
        self._rule_processors = self._initialize_rule_processors()
        
        # Cache configuration
        self._max_cache_size = 1000
        self._cache_ttl = 3600  # 1 hour
        
        # Logger
        self._logger = logging.getLogger(__name__)
        
        # Collect syntax error violations per file to surface in results
        self._syntax_error_violations: Dict[str, List[Violation]] = {}
    
    def _initialize_rule_processors(self) -> Dict[str, Any]:
        """Initialize rule processors for each category."""
        processors = {}
        
        # Import rule validators dynamically
        try:
            from .rules.basic_work import BasicWorkValidator
            processors['basic_work'] = BasicWorkValidator()
        except ImportError:
            pass
        
        try:
            from .rules.requirements import RequirementsValidator
            processors['requirements'] = RequirementsValidator()
        except ImportError:
            pass
        
        try:
            from .rules.privacy import PrivacyValidator
            processors['privacy_security'] = PrivacyValidator()
        except ImportError:
            pass
        
        # Add more processors as needed
        return processors
    
    def _get_file_hash(self, file_path: str) -> str:
        """Get hash of file content for cache invalidation."""
        if file_path not in self._file_hash_cache:
            try:
                with open(file_path, 'rb') as f:
                    content = f.read()
                    self._file_hash_cache[file_path] = hashlib.md5(content).hexdigest()
            except Exception:
                self._file_hash_cache[file_path] = ""
        
        return self._file_hash_cache[file_path]
    
    def _get_cached_ast(self, file_path: str) -> Optional[ast.AST]:
        """Get cached AST if available and valid."""
        file_hash = self._get_file_hash(file_path)
        current_time = time.time()
        
        if file_path in self._ast_cache:
            cached_ast, cache_time = self._ast_cache[file_path]
            
            # Check if cache is still valid
            if current_time - cache_time < self._cache_ttl:
                self._metrics["cache_hits"] += 1
                return cached_ast
            else:
                # Cache expired, remove it
                del self._ast_cache[file_path]
        
        self._metrics["cache_misses"] += 1
        return None
    
    def _cache_ast(self, file_path: str, tree: ast.AST):
        """Cache AST for future use."""
        current_time = time.time()
        
        # Limit cache size
        if len(self._ast_cache) >= self._max_cache_size:
            # Remove oldest entries
            oldest_key = min(self._ast_cache.keys(), 
                           key=lambda k: self._ast_cache[k][1])
            del self._ast_cache[oldest_key]
        
        self._ast_cache[file_path] = (tree, current_time)
    
    def _parse_ast(self, file_path: str, content: str) -> ast.AST:
        """Parse file content into AST with caching."""
        # Check cache first
        cached_ast = self._get_cached_ast(file_path)
        if cached_ast is not None:
            return cached_ast
        
        # Parse AST
        start_time = time.time()
        try:
            tree = ast.parse(content, filename=file_path)
            self._cache_ast(file_path, tree)
            
            parse_time = time.time() - start_time
            self._metrics["ast_parsing_time"] += parse_time
            
            return tree
        except SyntaxError as e:
            # Handle syntax errors as critical violations
            violation = Violation(
                rule_id="syntax_error",
                rule_name="Syntax Error",
                rule_number=14,
                severity=Severity.ERROR,
                message=f"Syntax error in file: {e.msg}",
                file_path=file_path,
                line_number=e.lineno or 0,
                column_number=e.offset or 0,
                code_snippet=content.split('\n')[e.lineno - 1] if e.lineno else "",
                fix_suggestion="Fix syntax errors before validation"
            )
            # Stash violation to include in ValidationResult
            self._syntax_error_violations.setdefault(file_path, []).append(violation)
            
            # Create a minimal AST for error handling
            tree = ast.parse("pass", filename=file_path)
            return tree
    
    def _process_rule_category(self, category: str, tree: ast.AST, 
                              content: str, file_path: str) -> List[Violation]:
        """Process rules for a specific category."""
        violations = []
        
        try:
            # Get rule configuration
            rule_config = self.config_manager.get_rule_config(category)
            rules = rule_config.get("rules", [])
            
            if not rules:
                return violations
            
            # Get pattern configuration
            pattern_config = self.config_manager.get_pattern_config(category)
            patterns = pattern_config.get("patterns", {})
            
            # Use rule processor if available
            if category in self._rule_processors:
                processor = self._rule_processors[category]
                if hasattr(processor, 'validate_all'):
                    category_violations = processor.validate_all(tree, content, file_path)
                    violations.extend(category_violations)
            else:
                # Fallback to pattern-based validation
                violations.extend(self._pattern_based_validation(
                    tree, content, file_path, patterns, rules
                ))
        
        except Exception as e:
            # Log error but don't fail validation
            self._logger.warning(f"Error processing category %s: %s", category, e)
        
        return violations
    
    def _pattern_based_validation(self, tree: ast.AST, content: str, 
                                 file_path: str, patterns: Dict[str, Any], 
                                 rules: List[int]) -> List[Violation]:
        """Fallback pattern-based validation."""
        violations = []
        
        for pattern_name, pattern_data in patterns.items():
            try:
                if "regex" in pattern_data:
                    # Regex-based validation
                    regex = pattern_data["regex"]
                    for match in re.finditer(regex, content):
                        violation = Violation(
                            rule_id=f"rule_{rules[0]:03d}" if rules else "unknown",
                            rule_name=pattern_data.get("message", "Pattern violation"),
                            rule_number=rules[0] if rules else 0,
                            severity=Severity(pattern_data.get("severity", "warning")),
                            message=pattern_data.get("message", "Pattern violation detected"),
                            file_path=file_path,
                            line_number=content[:match.start()].count('\n') + 1,
                            column_number=match.start() - content.rfind('\n', 0, match.start()) - 1,
                            code_snippet=match.group(),
                            fix_suggestion=f"Fix {pattern_name} violation"
                        )
                        violations.append(violation)
                
                elif "keywords" in pattern_data:
                    # Keyword-based validation
                    keywords = pattern_data["keywords"]
                    for keyword in keywords:
                        if keyword in content:
                            violation = Violation(
                                rule_id=f"rule_{rules[0]:03d}" if rules else "unknown",
                                rule_name=pattern_data.get("message", "Keyword violation"),
                                rule_number=rules[0] if rules else 0,
                                severity=Severity(pattern_data.get("severity", "warning")),
                                message=pattern_data.get("message", f"Keyword '{keyword}' detected"),
                                file_path=file_path,
                                line_number=1,
                                column_number=0,
                                code_snippet=keyword,
                                fix_suggestion=f"Review usage of '{keyword}'"
                            )
                            violations.append(violation)
            
            except Exception as e:
                self._logger.warning("Error in pattern validation %s: %s", pattern_name, e)
        
        return violations
    
    def validate_file(self, file_path: str, content: str = None) -> ValidationResult:
        """
        Validate a single Python file with optimized performance.
        
        Args:
            file_path: Path to the Python file to validate
            
        Returns:
            ValidationResult containing all violations found
        """
        start_time = time.time()
        
        if content is None:
            try:
                # Read file content
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                raise IOError(f"Could not read file {file_path}: {e}")
        
        # Parse AST with caching
        tree = self._parse_ast(file_path, content)
        
        # Get all categories to process
        categories = self.config_manager.get_all_categories()
        
        # Process rules in parallel
        violations = []
        rule_start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=min(len(categories), 8)) as executor:
            # Submit all category processing tasks
            future_to_category = {
                executor.submit(self._process_rule_category, category, tree, content, file_path): category
                for category in categories
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_category):
                category = future_to_category[future]
                try:
                    category_violations = future.result()
                    violations.extend(category_violations)
                except Exception as e:
                    self._logger.error("Error processing category %s: %s", category, e)
        
        # Include any syntax error violations detected during AST parsing
        if file_path in self._syntax_error_violations:
            violations.extend(self._syntax_error_violations.pop(file_path, []))
        
        rule_processing_time = time.time() - rule_start_time
        self._metrics["rule_processing_time"] += rule_processing_time
        
        # Calculate metrics
        violations_by_severity = self._count_violations_by_severity(violations)
        total_violations = len(violations)
        compliance_score = self._calculate_compliance_score(violations, total_violations)
        processing_time = time.time() - start_time
        
        # Update metrics
        self._metrics["files_processed"] += 1
        self._metrics["total_processing_time"] += processing_time
        
        return ValidationResult(
            file_path=file_path,
            total_violations=total_violations,
            violations_by_severity=violations_by_severity,
            violations=violations,
            processing_time=processing_time,
            compliance_score=compliance_score
        )
    
    def validate_directory(self, directory_path: str, recursive: bool = True) -> Dict[str, ValidationResult]:
        """
        Validate all Python files in a directory with parallel processing.
        
        Args:
            directory_path: Path to directory to validate
            recursive: Whether to search subdirectories recursively
            
        Returns:
            Dictionary mapping file paths to validation results
        """
        results = {}
        directory = Path(directory_path)
        
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        # Find Python files
        pattern = "**/*.py" if recursive else "*.py"
        python_files = list(directory.glob(pattern))
        
        if not python_files:
            self._logger.info("No Python files found in %s", directory_path)
            return results
        
        self._logger.info("Validating %d Python files...", len(python_files))
        
        # Process files in parallel
        with ThreadPoolExecutor(max_workers=min(len(python_files), 16)) as executor:
            # Submit all file validation tasks
            future_to_file = {
                executor.submit(self.validate_file, str(file_path)): file_path
                for file_path in python_files
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    result = future.result()
                    results[str(file_path)] = result
                    self._logger.info("[OK] %s: %s%% compliance", file_path.name, result.compliance_score)
                except Exception as e:
                    self._logger.error("[ERROR] Error validating %s: %s", file_path, e)
        
        return results
    
    def _count_violations_by_severity(self, violations: List[Violation]) -> Dict[Severity, int]:
        """Count violations by severity level."""
        counts = {Severity.ERROR: 0, Severity.WARNING: 0, Severity.INFO: 0}
        for violation in violations:
            counts[violation.severity] += 1
        return counts
    
    def _calculate_compliance_score(self, violations: List[Violation], total_violations: int) -> float:
        """Calculate compliance score based on violations."""
        if total_violations == 0:
            return 100.0
        
        # Weight violations by severity
        error_weight = 3
        warning_weight = 2
        info_weight = 1
        
        weighted_violations = 0
        for violation in violations:
            if violation.severity == Severity.ERROR:
                weighted_violations += error_weight
            elif violation.severity == Severity.WARNING:
                weighted_violations += warning_weight
            else:
                weighted_violations += info_weight
        
        # Calculate score (higher is better)
        max_possible_violations = total_violations * error_weight
        score = max(0, 100 - (weighted_violations / max_possible_violations * 100))
        return round(score, 2)
    
    def generate_report(self, results: Dict[str, ValidationResult], 
                       output_format: str = "console") -> str:
        """
        Generate a validation report.
        
        Args:
            results: Dictionary of validation results
            output_format: Format of the report ("console", "json", "html", "markdown")
            
        Returns:
            Generated report as string
        """
        return self.reporter.generate_report(results, output_format, self.config_manager.base_config)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        metrics = self._metrics.copy()
        
        if metrics["files_processed"] > 0:
            metrics["avg_processing_time"] = metrics["total_processing_time"] / metrics["files_processed"]
            metrics["avg_ast_parsing_time"] = metrics["ast_parsing_time"] / metrics["files_processed"]
            metrics["avg_rule_processing_time"] = metrics["rule_processing_time"] / metrics["files_processed"]
            metrics["cache_hit_rate"] = metrics["cache_hits"] / (metrics["cache_hits"] + metrics["cache_misses"])
        
        metrics["cache_size"] = len(self._ast_cache)
        metrics["config_categories"] = len(self.config_manager.get_all_categories())
        
        return metrics
    
    def clear_cache(self):
        """Clear all caches."""
        self._ast_cache.clear()
        self._file_hash_cache.clear()
        self._rule_cache.clear()
        self._pattern_cache.clear()
        self._metrics = {
            "files_processed": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_processing_time": 0.0,
            "ast_parsing_time": 0.0,
            "rule_processing_time": 0.0
        }
