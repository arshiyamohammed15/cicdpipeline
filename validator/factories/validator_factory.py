"""
Validator Factory for Dependency Injection

This module provides a factory pattern for creating validators,
reducing tight coupling and enabling dependency injection.
"""

import logging
from typing import Dict, Type, List, Optional, Any
from abc import ABC, abstractmethod

from ..base_validator import BaseRuleValidator
from ..models import Violation

logger = logging.getLogger(__name__)


class ValidatorFactory:
    """
    Factory for creating rule validators with dependency injection support.
    
    This factory reduces tight coupling by centralizing validator creation
    and allowing dependency injection for testing and extensibility.
    """
    
    def __init__(self):
        """Initialize the validator factory with registered validators."""
        self._validators: Dict[str, Type[BaseRuleValidator]] = {}
        self._register_default_validators()
    
    def _register_default_validators(self) -> None:
        """Register all default validators."""
        try:
            from ..rules.basic_work import BasicWorkValidator
            self.register('basic_work', BasicWorkValidator)
        except ImportError:
            logger.debug("BasicWorkValidator not available")
        
        try:
            from ..rules.requirements import RequirementsValidator
            self.register('requirements', RequirementsValidator)
        except ImportError:
            logger.debug("RequirementsValidator not available")
        
        try:
            from ..rules.privacy import PrivacyValidator
            self.register('privacy', PrivacyValidator)
        except ImportError:
            logger.debug("PrivacyValidator not available")
        
        try:
            from ..rules.performance import PerformanceValidator
            self.register('performance', PerformanceValidator)
        except ImportError:
            logger.debug("PerformanceValidator not available")
        
        try:
            from ..rules.architecture import ArchitectureValidator
            self.register('architecture', ArchitectureValidator)
        except ImportError:
            logger.debug("ArchitectureValidator not available")
        
        try:
            from ..rules.testing_safety import TestingSafetyValidator
            self.register('testing_safety', TestingSafetyValidator)
        except ImportError:
            logger.debug("TestingSafetyValidator not available")
        
        try:
            from ..rules.code_quality import CodeQualityValidator
            self.register('code_quality', CodeQualityValidator)
        except ImportError:
            logger.debug("CodeQualityValidator not available")
        
        try:
            from ..rules.system_design import SystemDesignValidator
            self.register('system_design', SystemDesignValidator)
        except ImportError:
            logger.debug("SystemDesignValidator not available")
        
        try:
            from ..rules.problem_solving import ProblemSolvingValidator
            self.register('problem_solving', ProblemSolvingValidator)
        except ImportError:
            logger.debug("ProblemSolvingValidator not available")
        
        try:
            from ..rules.platform import PlatformValidator
            self.register('platform', PlatformValidator)
        except ImportError:
            logger.debug("PlatformValidator not available")
        
        try:
            from ..rules.teamwork import TeamworkValidator
            self.register('teamwork', TeamworkValidator)
        except ImportError:
            logger.debug("TeamworkValidator not available")
        
        try:
            from ..rules.code_review import CodeReviewValidator
            self.register('code_review', CodeReviewValidator)
        except ImportError:
            logger.debug("CodeReviewValidator not available")
        
        try:
            from ..rules.api_contracts import APIContractsValidator
            self.register('api_contracts', APIContractsValidator)
        except ImportError:
            logger.debug("APIContractsValidator not available")
        
        try:
            from ..rules.coding_standards import CodingStandardsValidator
            self.register('coding_standards', CodingStandardsValidator)
        except ImportError:
            logger.debug("CodingStandardsValidator not available")
        
        try:
            from ..rules.comments import CommentsValidator
            self.register('comments', CommentsValidator)
        except ImportError:
            logger.debug("CommentsValidator not available")
        
        try:
            from ..rules.folder_standards import FolderStandardsValidator
            self.register('folder_standards', FolderStandardsValidator)
        except ImportError:
            logger.debug("FolderStandardsValidator not available")
        
        try:
            from ..rules.logging import LoggingValidator
            self.register('logging', LoggingValidator)
        except ImportError:
            logger.debug("LoggingValidator not available")
        
        try:
            from ..rules.exception_handling import ExceptionHandlingValidator
            self.register('exception_handling', ExceptionHandlingValidator)
        except ImportError:
            logger.debug("ExceptionHandlingValidator not available")
        
        try:
            from ..rules.typescript import TypeScriptValidator
            self.register('typescript', TypeScriptValidator)
        except ImportError:
            logger.debug("TypeScriptValidator not available")
        
        try:
            from ..rules.storage_governance import StorageGovernanceValidator
            self.register('storage_governance', StorageGovernanceValidator)
        except ImportError:
            logger.debug("StorageGovernanceValidator not available")
    
    def register(self, name: str, validator_class: Type[BaseRuleValidator]) -> None:
        """
        Register a validator class.
        
        Args:
            name: Name identifier for the validator
            validator_class: Validator class to register
        """
        self._validators[name] = validator_class
        logger.debug(f"Registered validator: {name}")
    
    def create(self, name: str, rule_config: Optional[Dict[str, Any]] = None) -> Optional[BaseRuleValidator]:
        """
        Create a validator instance.
        
        Args:
            name: Name of the validator to create
            rule_config: Optional rule configuration
            
        Returns:
            Validator instance or None if not found
        """
        if name not in self._validators:
            logger.warning(f"Validator not found: {name}")
            return None
        
        validator_class = self._validators[name]
        
        # Create default config if not provided
        if rule_config is None:
            rule_config = {
                "rules": [],
                "category": name,
                "priority": "medium",
                "description": f"{name} validation rules"
            }
        
        try:
            return validator_class(rule_config)
        except Exception as e:
            logger.error(f"Failed to create validator {name}: {e}", exc_info=True)
            return None
    
    def get_available_validators(self) -> List[str]:
        """
        Get list of available validator names.
        
        Returns:
            List of validator names
        """
        return list(self._validators.keys())
    
    def has_validator(self, name: str) -> bool:
        """
        Check if a validator is registered.
        
        Args:
            name: Validator name to check
            
        Returns:
            True if validator is registered
        """
        return name in self._validators


# Global factory instance
_default_factory: Optional[ValidatorFactory] = None


def get_validator_factory() -> ValidatorFactory:
    """
    Get the default validator factory instance.
    
    Returns:
        ValidatorFactory instance
    """
    global _default_factory
    if _default_factory is None:
        _default_factory = ValidatorFactory()
    return _default_factory


def set_validator_factory(factory: ValidatorFactory) -> None:
    """
    Set a custom validator factory (useful for testing).
    
    Args:
        factory: ValidatorFactory instance to use
    """
    global _default_factory
    _default_factory = factory

