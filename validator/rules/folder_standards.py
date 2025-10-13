"""
Folder Standards Constitution Validator

Validates compliance with the ZeroUI 2.0 Folder Standards Constitution.
Covers project structure, path resolution, and organization.
"""

import re
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from ..models import Violation, Severity


class FolderStandardsValidator:
    """Validates folder structure and organization standards."""
    
    def __init__(self):
        self.rules = {
            'R054': self._validate_path_resolution,
            'R055': self._validate_directory_structure,
            'R056': self._validate_package_structure,
            'R057': self._validate_import_organization,
            'R058': self._validate_module_boundaries,
            'R059': self._validate_dependency_management,
            'R060': self._validate_configuration_management,
            'R061': self._validate_test_organization,
            'R062': self._validate_documentation_organization,
            'R082': self._validate_storage_rule
        }
        
        # Allowed server and storage names
        self.allowed_names = [
            'ZeroUIClientServer', 'ZeroUIProductServer', 'ZeroUILocalServer', 'ZeroUISharedServer',
            'ZeroUIClientStorage', 'ZeroUIProductStorage', 'ZeroUILocalStorage', 'ZeroUISharedStorage'
        ]
        
        # Allowed subfolders
        self.allowed_subfolders = ['servers/', 'storage/']
    
    def validate(self, file_path: str, content: str) -> List[Violation]:
        """Validate folder standards compliance for a file."""
        violations = []
        
        # Check path resolution
        violations.extend(self._validate_path_resolution(content, file_path))
        
        # Check directory structure
        violations.extend(self._validate_directory_structure(content, file_path))
        
        # Check package structure
        violations.extend(self._validate_package_structure(content, file_path))
        
        # Check import organization
        violations.extend(self._validate_import_organization(content, file_path))
        
        # Check module boundaries
        violations.extend(self._validate_module_boundaries(content, file_path))
        
        # Check dependency management
        violations.extend(self._validate_dependency_management(content, file_path))
        
        # Check configuration management
        violations.extend(self._validate_configuration_management(content, file_path))
        
        # Check test organization
        violations.extend(self._validate_test_organization(content, file_path))
        
        # Check documentation organization
        violations.extend(self._validate_documentation_organization(content, file_path))
        
        # Check storage rule
        violations.extend(self._validate_storage_rule(content, file_path))
        
        return violations
    
    def _validate_path_resolution(self, content: str, file_path: str) -> List[Violation]:
        """Validate path resolution via ZEROUI_ROOT."""
        violations = []
        
        # Check for hardcoded paths
        hardcoded_path_patterns = [
            r'["\']/[^"\']*["\']',  # Absolute paths
            r'["\']\.\./[^"\']*["\']',  # Relative paths with ..
            r'["\']\./[^"\']*["\']',  # Relative paths with .
        ]
        
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            for pattern in hardcoded_path_patterns:
                if re.search(pattern, line):
                    # Check if it's using ZEROUI_ROOT
                    if 'ZEROUI_ROOT' not in line and 'config/paths.json' not in line:
                        violations.append(Violation(
                            rule_id='R054',
                            file_path=file_path,
                            line_number=line_num,
                            message='Resolve all paths via ZEROUI_ROOT + config/paths.json; never hardcode paths',
                            severity=Severity.ERROR,
                            category='structure'
                        ))
        
        return violations
    
    def _validate_directory_structure(self, content: str, file_path: str) -> List[Violation]:
        """Validate directory structure compliance."""
        violations = []
        
        # Check if file is in allowlisted subfolders
        file_path_obj = Path(file_path)
        path_parts = file_path_obj.parts
        
        # Check if any part of the path contains allowed subfolders
        in_allowed_folder = any(
            any(allowed in str(part) for allowed in self.allowed_subfolders)
            for part in path_parts
        )
        
        # Skip validation for certain files
        skip_files = ['README.md', 'LICENSE', '.gitignore', 'requirements.txt', 'package.json']
        if file_path_obj.name in skip_files:
            return violations
        
        # Check if file is outside allowlisted folders
        if not in_allowed_folder and len(path_parts) > 1:
            violations.append(Violation(
                rule_id='R055',
                file_path=file_path,
                line_number=1,
                message='Only write under allowlisted subfolders: servers/*/ and storage/*/',
                severity=Severity.ERROR,
                category='structure'
            ))
        
        return violations
    
    def _validate_package_structure(self, content: str, file_path: str) -> List[Violation]:
        """Validate package structure compliance."""
        violations = []
        
        # Check for new top-level names
        if file_path.endswith('.py'):
            # Look for class definitions
            class_pattern = r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)'
            for match in re.finditer(class_pattern, content):
                class_name = match.group(1)
                if class_name not in self.allowed_names and not class_name.startswith('_'):
                    violations.append(Violation(
                        rule_id='R056',
                        file_path=file_path,
                        line_number=content[:match.start()].count('\n') + 1,
                        message=f'Never create new top-level names besides the eight allowed server/storage names',
                        severity=Severity.ERROR,
                        category='structure'
                    ))
        
        return violations
    
    def _validate_import_organization(self, content: str, file_path: str) -> List[Violation]:
        """Validate import organization and junction usage."""
        violations = []
        
        # Check for persistence via junction
        if 'import' in content and 'data' in content:
            # Look for imports that should go through junction
            junction_patterns = [
                r'from\s+([^\\s]+)\s+import',
                r'import\s+([^\\s]+)'
            ]
            
            for pattern in junction_patterns:
                for match in re.finditer(pattern, content):
                    import_name = match.group(1)
                    if 'storage' in import_name.lower() and 'data/' not in import_name:
                        violations.append(Violation(
                            rule_id='R057',
                            file_path=file_path,
                            line_number=content[:match.start()].count('\n') + 1,
                            message='Persistence MUST go via <server>/data/ junction to paired storage',
                            severity=Severity.ERROR,
                            category='structure'
                        ))
        
        return violations
    
    def _validate_module_boundaries(self, content: str, file_path: str) -> List[Violation]:
        """Validate module boundaries and circular dependencies."""
        violations = []
        
        # Check for circular import patterns
        if 'import' in content:
            # Look for imports that might create circular dependencies
            import_patterns = [
                r'from\s+([^\\s]+)\s+import',
                r'import\s+([^\\s]+)'
            ]
            
            for pattern in import_patterns:
                for match in re.finditer(pattern, content):
                    import_name = match.group(1)
                    # Check for potential circular imports
                    if 'circular' in import_name.lower() or 'loop' in import_name.lower():
                        violations.append(Violation(
                            rule_id='R058',
                            file_path=file_path,
                            line_number=content[:match.start()].count('\n') + 1,
                            message='Respect module boundaries and avoid circular dependencies',
                            severity=Severity.WARNING,
                            category='structure'
                        ))
        
        return violations
    
    def _validate_dependency_management(self, content: str, file_path: str) -> List[Violation]:
        """Validate dependency management compliance."""
        violations = []
        
        # Check if this is a dependency file
        if self._is_dependency_file(file_path):
            # Check for pip-tools usage
            if 'requirements.txt' in file_path:
                if 'pip-tools' not in content.lower() and 'lock' not in content.lower():
                    violations.append(Violation(
                        rule_id='R059',
                        file_path=file_path,
                        line_number=1,
                        message='Use pip-tools lock with hashes; no unpinned dependencies',
                        severity=Severity.ERROR,
                        category='structure'
                    ))
            
            # Check for unpinned dependencies
            if '==' not in content and '~=' not in content and '>=' not in content:
                violations.append(Violation(
                    rule_id='R059',
                    file_path=file_path,
                    line_number=1,
                    message='Use pip-tools lock with hashes; no unpinned dependencies',
                    severity=Severity.ERROR,
                    category='structure'
                ))
        
        return violations
    
    def _validate_configuration_management(self, content: str, file_path: str) -> List[Violation]:
        """Validate configuration management."""
        violations = []
        
        # Check if this is a configuration file
        if self._is_config_file(file_path):
            # Check if it's in the right location
            if 'config/' not in file_path and 'configuration/' not in file_path:
                violations.append(Violation(
                    rule_id='R060',
                    file_path=file_path,
                    line_number=1,
                    message='Configuration files must be in designated config directories',
                    severity=Severity.WARNING,
                    category='structure'
                ))
        
        return violations
    
    def _validate_test_organization(self, content: str, file_path: str) -> List[Violation]:
        """Validate test organization."""
        violations = []
        
        # Check if this is a test file
        if self._is_test_file(file_path):
            # Check if it's in the right location
            if 'test/' not in file_path and 'tests/' not in file_path and 'spec/' not in file_path:
                violations.append(Violation(
                    rule_id='R061',
                    file_path=file_path,
                    line_number=1,
                    message='Tests must be organized in designated test directories',
                    severity=Severity.WARNING,
                    category='structure'
                ))
        
        return violations
    
    def _validate_documentation_organization(self, content: str, file_path: str) -> List[Violation]:
        """Validate documentation organization."""
        violations = []
        
        # Check if this is a documentation file
        if self._is_documentation_file(file_path):
            # Check if it's in the right location
            if 'docs/' not in file_path and 'documentation/' not in file_path:
                violations.append(Violation(
                    rule_id='R062',
                    file_path=file_path,
                    line_number=1,
                    message='Documentation must be organized in designated docs directories',
                    severity=Severity.WARNING,
                    category='structure'
                ))
        
        return violations
    
    def _validate_storage_rule(self, content: str, file_path: str) -> List[Violation]:
        """Validate storage rule (≤256KB in DB)."""
        violations = []
        
        # Check for database operations
        if 'database' in content.lower() or 'db' in content.lower():
            # Look for file size indicators
            size_patterns = [
                r'(\d+)\s*KB',
                r'(\d+)\s*MB',
                r'(\d+)\s*GB',
                r'size\s*[=:]\s*(\d+)',
                r'length\s*[=:]\s*(\d+)'
            ]
            
            for pattern in size_patterns:
                for match in re.finditer(pattern, content):
                    size_value = int(match.group(1))
                    size_unit = match.group(0).upper()
                    
                    # Convert to bytes for comparison
                    if 'KB' in size_unit:
                        size_bytes = size_value * 1024
                    elif 'MB' in size_unit:
                        size_bytes = size_value * 1024 * 1024
                    elif 'GB' in size_unit:
                        size_bytes = size_value * 1024 * 1024 * 1024
                    else:
                        size_bytes = size_value
                    
                    # Check if size exceeds 256KB
                    if size_bytes > 256000:  # 256KB in bytes
                        violations.append(Violation(
                            rule_id='R082',
                            file_path=file_path,
                            line_number=content[:match.start()].count('\n') + 1,
                            message='Database vs files choice follows Storage Constitution (≤256KB in DB)',
                            severity=Severity.ERROR,
                            category='structure'
                        ))
        
        return violations
    
    def _is_dependency_file(self, file_path: str) -> bool:
        """Check if file is a dependency management file."""
        dependency_files = [
            'requirements.txt', 'requirements.in', 'Pipfile', 'Pipfile.lock',
            'poetry.lock', 'yarn.lock', 'package.json', 'package-lock.json'
        ]
        return any(file_path.endswith(f) for f in dependency_files)
    
    def _is_config_file(self, file_path: str) -> bool:
        """Check if file is a configuration file."""
        config_files = [
            'config.json', 'config.yaml', 'config.yml', 'config.ini',
            'settings.py', 'settings.json', '.env', 'environment.yml'
        ]
        return any(file_path.endswith(f) for f in config_files)
    
    def _is_test_file(self, file_path: str) -> bool:
        """Check if file is a test file."""
        test_patterns = ['test_', '_test', '.test.', '.spec.']
        return any(pattern in file_path.lower() for pattern in test_patterns)
    
    def _is_documentation_file(self, file_path: str) -> bool:
        """Check if file is a documentation file."""
        doc_files = [
            'README.md', 'README.rst', 'README.txt', 'CHANGELOG.md',
            'CONTRIBUTING.md', 'LICENSE', 'NOTICE', 'AUTHORS'
        ]
        return any(file_path.endswith(f) for f in doc_files)
