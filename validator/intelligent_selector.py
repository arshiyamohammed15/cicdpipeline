#!/usr/bin/env python3
"""
Intelligent rule selector for context-aware validation.

This module provides intelligent rule selection based on file context,
code patterns, and project characteristics.
"""

import ast
import re
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class FileType(Enum):
    """Types of files based on content analysis."""
    API_ENDPOINT = "api_endpoint"
    DATABASE_MODEL = "database_model"
    UI_COMPONENT = "ui_component"
    BUSINESS_LOGIC = "business_logic"
    UTILITY = "utility"
    TEST = "test"
    CONFIG = "config"
    UNKNOWN = "unknown"


class ProjectType(Enum):
    """Types of projects based on analysis."""
    WEB_APPLICATION = "web_application"
    API_SERVICE = "api_service"
    DATA_PIPELINE = "data_pipeline"
    MACHINE_LEARNING = "machine_learning"
    DESKTOP_APPLICATION = "desktop_application"
    UNKNOWN = "unknown"


@dataclass
class FileContext:
    """Context information about a file."""
    file_path: str
    file_type: FileType
    project_type: ProjectType
    imports: List[str]
    functions: List[str]
    classes: List[str]
    has_database_code: bool
    has_api_code: bool
    has_ui_code: bool
    has_ai_code: bool
    has_security_code: bool
    complexity_score: float
    size_category: str  # small, medium, large


class IntelligentRuleSelector:
    """
    Intelligent rule selector that chooses relevant rules based on context.
    
    This selector analyzes file content and project structure to determine
    which rules are most relevant for validation.
    """
    
    def __init__(self, config_manager):
        """
        Initialize the intelligent rule selector.
        
        Args:
            config_manager: Enhanced configuration manager
        """
        self.config_manager = config_manager
        self.rule_relevance_scores: Dict[str, Dict[str, float]] = {}
        self._initialize_relevance_scores()
    
    def _initialize_relevance_scores(self):
        """Initialize rule relevance scores for different contexts."""
        # Define relevance scores for different file types and rule categories
        self.rule_relevance_scores = {
            FileType.API_ENDPOINT.value: {
                "api_contracts": 1.0,
                "privacy_security": 0.9,
                "performance": 0.8,
                "requirements": 0.7,
                "basic_work": 0.6,
                "code_quality": 0.5,
                "testing_safety": 0.4,
                "teamwork": 0.3,
                "architecture": 0.2,
                "problem_solving": 0.1
            },
            FileType.DATABASE_MODEL.value: {
                "privacy_security": 1.0,
                "api_contracts": 0.8,
                "performance": 0.7,
                "basic_work": 0.6,
                "code_quality": 0.5,
                "requirements": 0.4,
                "testing_safety": 0.3,
                "architecture": 0.2,
                "teamwork": 0.1,
                "problem_solving": 0.1
            },
            FileType.UI_COMPONENT.value: {
                "teamwork": 1.0,
                "privacy_security": 0.8,
                "performance": 0.7,
                "basic_work": 0.6,
                "code_quality": 0.5,
                "requirements": 0.4,
                "testing_safety": 0.3,
                "architecture": 0.2,
                "api_contracts": 0.1,
                "problem_solving": 0.1
            },
            FileType.BUSINESS_LOGIC.value: {
                "requirements": 1.0,
                "basic_work": 0.9,
                "code_quality": 0.8,
                "performance": 0.7,
                "privacy_security": 0.6,
                "testing_safety": 0.5,
                "architecture": 0.4,
                "problem_solving": 0.3,
                "api_contracts": 0.2,
                "teamwork": 0.1
            },
            FileType.UTILITY.value: {
                "code_quality": 1.0,
                "performance": 0.8,
                "basic_work": 0.7,
                "requirements": 0.6,
                "testing_safety": 0.5,
                "privacy_security": 0.4,
                "architecture": 0.3,
                "api_contracts": 0.2,
                "teamwork": 0.1,
                "problem_solving": 0.1
            },
            FileType.TEST.value: {
                "testing_safety": 1.0,
                "code_quality": 0.8,
                "basic_work": 0.7,
                "requirements": 0.6,
                "performance": 0.5,
                "privacy_security": 0.4,
                "architecture": 0.3,
                "api_contracts": 0.2,
                "teamwork": 0.1,
                "problem_solving": 0.1
            },
            FileType.CONFIG.value: {
                "basic_work": 1.0,
                "privacy_security": 0.9,
                "requirements": 0.8,
                "code_quality": 0.7,
                "architecture": 0.6,
                "performance": 0.5,
                "testing_safety": 0.4,
                "api_contracts": 0.3,
                "teamwork": 0.2,
                "problem_solving": 0.1
            }
        }
    
    def analyze_file_context(self, file_path: str, content: str) -> FileContext:
        """
        Analyze file context to determine its characteristics.
        
        Args:
            file_path: Path to the file
            content: File content
            
        Returns:
            FileContext object with analysis results
        """
        try:
            tree = ast.parse(content, filename=file_path)
        except SyntaxError:
            # Handle syntax errors gracefully
            tree = ast.parse("pass", filename=file_path)
        
        # Analyze imports
        imports = self._analyze_imports(tree)
        
        # Analyze functions and classes
        functions = self._analyze_functions(tree)
        classes = self._analyze_classes(tree)
        
        # Determine file type
        file_type = self._determine_file_type(content, imports, functions, classes)
        
        # Determine project type
        project_type = self._determine_project_type(imports, content)
        
        # Analyze code characteristics
        has_database_code = self._has_database_code(content, imports)
        has_api_code = self._has_api_code(content, imports)
        has_ui_code = self._has_ui_code(content, imports)
        has_ai_code = self._has_ai_code(content, imports)
        has_security_code = self._has_security_code(content, imports)
        
        # Calculate complexity score
        complexity_score = self._calculate_complexity_score(tree)
        
        # Determine size category
        size_category = self._determine_size_category(len(content.split('\n')))
        
        return FileContext(
            file_path=file_path,
            file_type=file_type,
            project_type=project_type,
            imports=imports,
            functions=functions,
            classes=classes,
            has_database_code=has_database_code,
            has_api_code=has_api_code,
            has_ui_code=has_ui_code,
            has_ai_code=has_ai_code,
            has_security_code=has_security_code,
            complexity_score=complexity_score,
            size_category=size_category
        )
    
    def _analyze_imports(self, tree: ast.AST) -> List[str]:
        """Analyze imports in the AST."""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        return imports
    
    def _analyze_functions(self, tree: ast.AST) -> List[str]:
        """Analyze function definitions in the AST."""
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)
        return functions
    
    def _analyze_classes(self, tree: ast.AST) -> List[str]:
        """Analyze class definitions in the AST."""
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append(node.name)
        return classes
    
    def _determine_file_type(self, content: str, imports: List[str], 
                           functions: List[str], classes: List[str]) -> FileType:
        """Determine the type of file based on content analysis."""
        content_lower = content.lower()
        
        # Check for API endpoints
        api_patterns = ['@app.route', '@router', 'fastapi', 'flask', 'django', 'endpoint', 'api']
        if any(pattern in content_lower for pattern in api_patterns):
            return FileType.API_ENDPOINT
        
        # Check for database models
        db_patterns = ['model', 'table', 'sqlalchemy', 'django.db', 'orm', 'database']
        if any(pattern in content_lower for pattern in db_patterns):
            return FileType.DATABASE_MODEL
        
        # Check for UI components
        ui_patterns = ['tkinter', 'pyqt', 'kivy', 'streamlit', 'dash', 'gui', 'widget']
        if any(pattern in content_lower for pattern in ui_patterns):
            return FileType.UI_COMPONENT
        
        # Check for test files
        test_patterns = ['test_', 'test.py', 'pytest', 'unittest', 'assert']
        if any(pattern in content_lower for pattern in test_patterns):
            return FileType.TEST
        
        # Check for config files
        config_patterns = ['config', 'settings', 'configuration', 'env']
        if any(pattern in content_lower for pattern in config_patterns):
            return FileType.CONFIG
        
        # Check for utility functions
        utility_patterns = ['util', 'helper', 'common', 'shared']
        if any(pattern in content_lower for pattern in utility_patterns):
            return FileType.UTILITY
        
        # Default to business logic
        return FileType.BUSINESS_LOGIC
    
    def _determine_project_type(self, imports: List[str], content: str) -> ProjectType:
        """Determine the type of project based on imports and content."""
        content_lower = content.lower()
        
        # Check for web application
        web_patterns = ['flask', 'django', 'fastapi', 'tornado', 'bottle']
        if any(pattern in content_lower for pattern in web_patterns):
            return ProjectType.WEB_APPLICATION
        
        # Check for API service
        api_patterns = ['requests', 'urllib', 'httpx', 'aiohttp', 'rest']
        if any(pattern in content_lower for pattern in api_patterns):
            return ProjectType.API_SERVICE
        
        # Check for data pipeline
        data_patterns = ['pandas', 'numpy', 'spark', 'kafka', 'pipeline']
        if any(pattern in content_lower for pattern in data_patterns):
            return ProjectType.DATA_PIPELINE
        
        # Check for machine learning
        ml_patterns = ['tensorflow', 'pytorch', 'sklearn', 'keras', 'ml']
        if any(pattern in content_lower for pattern in ml_patterns):
            return ProjectType.MACHINE_LEARNING
        
        # Check for desktop application
        desktop_patterns = ['tkinter', 'pyqt', 'kivy', 'wxpython']
        if any(pattern in content_lower for pattern in desktop_patterns):
            return ProjectType.DESKTOP_APPLICATION
        
        return ProjectType.UNKNOWN
    
    def _has_database_code(self, content: str, imports: List[str]) -> bool:
        """Check if file contains database-related code."""
        db_patterns = ['sql', 'database', 'db', 'orm', 'model', 'table']
        return any(pattern in content.lower() for pattern in db_patterns)
    
    def _has_api_code(self, content: str, imports: List[str]) -> bool:
        """Check if file contains API-related code."""
        api_patterns = ['api', 'endpoint', 'route', 'request', 'response', 'http']
        return any(pattern in content.lower() for pattern in api_patterns)
    
    def _has_ui_code(self, content: str, imports: List[str]) -> bool:
        """Check if file contains UI-related code."""
        ui_patterns = ['gui', 'ui', 'widget', 'button', 'window', 'dialog']
        return any(pattern in content.lower() for pattern in ui_patterns)
    
    def _has_ai_code(self, content: str, imports: List[str]) -> bool:
        """Check if file contains AI-related code."""
        ai_patterns = ['ai', 'ml', 'neural', 'model', 'tensor', 'pytorch']
        return any(pattern in content.lower() for pattern in ai_patterns)
    
    def _has_security_code(self, content: str, imports: List[str]) -> bool:
        """Check if file contains security-related code."""
        security_patterns = ['auth', 'security', 'encrypt', 'hash', 'token', 'jwt']
        return any(pattern in content.lower() for pattern in security_patterns)
    
    def _calculate_complexity_score(self, tree: ast.AST) -> float:
        """Calculate complexity score for the code."""
        complexity = 0
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.Try)):
                complexity += 1
            elif isinstance(node, ast.FunctionDef):
                complexity += len(node.body)
            elif isinstance(node, ast.ClassDef):
                complexity += len(node.body)
        
        return min(complexity / 100.0, 1.0)  # Normalize to 0-1
    
    def _determine_size_category(self, line_count: int) -> str:
        """Determine size category based on line count."""
        if line_count < 50:
            return "small"
        elif line_count < 200:
            return "medium"
        else:
            return "large"
    
    def select_relevant_rules(self, context: FileContext, 
                            threshold: float = 0.5) -> List[str]:
        """
        Select relevant rules based on file context.
        
        Args:
            context: File context information
            threshold: Minimum relevance score threshold
            
        Returns:
            List of relevant rule category names
        """
        relevant_categories = []
        
        # Get base relevance scores for file type
        file_type_scores = self.rule_relevance_scores.get(
            context.file_type.value, {}
        )
        
        # Adjust scores based on additional context
        for category, base_score in file_type_scores.items():
            adjusted_score = base_score
            
            # Boost scores based on detected code patterns
            if category == "privacy_security" and context.has_security_code:
                adjusted_score += 0.2
            
            if category == "api_contracts" and context.has_api_code:
                adjusted_score += 0.2
            
            if category == "performance" and context.complexity_score > 0.7:
                adjusted_score += 0.2
            
            if category == "testing_safety" and context.file_type == FileType.TEST:
                adjusted_score += 0.3
            
            # Adjust based on project type
            if context.project_type == ProjectType.WEB_APPLICATION:
                if category in ["api_contracts", "privacy_security"]:
                    adjusted_score += 0.1
            
            elif context.project_type == ProjectType.MACHINE_LEARNING:
                if category in ["privacy_security", "performance"]:
                    adjusted_score += 0.1
            
            # Apply threshold
            if adjusted_score >= threshold:
                relevant_categories.append(category)
        
        return relevant_categories
    
    def get_rule_priorities(self, context: FileContext) -> Dict[str, float]:
        """
        Get rule priorities based on file context.
        
        Args:
            context: File context information
            
        Returns:
            Dictionary mapping rule categories to priority scores
        """
        priorities = {}
        
        # Get base relevance scores
        file_type_scores = self.rule_relevance_scores.get(
            context.file_type.value, {}
        )
        
        # Calculate priorities
        for category, base_score in file_type_scores.items():
            priority = base_score
            
            # Adjust based on context
            if category == "privacy_security" and context.has_security_code:
                priority += 0.2
            
            if category == "performance" and context.complexity_score > 0.7:
                priority += 0.2
            
            if category == "testing_safety" and context.file_type == FileType.TEST:
                priority += 0.3
            
            priorities[category] = min(priority, 1.0)  # Cap at 1.0
        
        return priorities
    
    def get_validation_strategy(self, context: FileContext) -> Dict[str, Any]:
        """
        Get validation strategy based on file context.
        
        Args:
            context: File context information
            
        Returns:
            Validation strategy configuration
        """
        strategy = {
            "file_type": context.file_type.value,
            "project_type": context.project_type.value,
            "relevant_categories": self.select_relevant_rules(context),
            "rule_priorities": self.get_rule_priorities(context),
            "validation_mode": "standard",
            "performance_mode": "balanced"
        }
        
        # Adjust strategy based on context
        if context.complexity_score > 0.8:
            strategy["performance_mode"] = "fast"
        
        if context.file_type == FileType.TEST:
            strategy["validation_mode"] = "strict"
        
        if context.has_security_code:
            strategy["validation_mode"] = "security_focused"
        
        return strategy
