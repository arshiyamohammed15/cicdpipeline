"""
Storage Governance Constitution Validator

Validates compliance with the ZeroUI 4-Plane Storage Constitution.
Enforces rules from storage-scripts/folder-business-rules.md v1.1.
"""

import re
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from ..models import Violation, Severity


class StorageGovernanceValidator:
    """Validates storage governance and 4-plane architecture compliance."""
    
    def __init__(self):
        self.rules = {
            'R216': self._validate_name_casing,
            'R217': self._validate_no_code_pii,
            'R218': self._validate_no_secrets,
            'R219': self._validate_jsonl_receipts,
            'R220': self._validate_time_partitions,
            'R221': self._validate_policy_signatures,
            'R222': self._validate_dual_storage,
            'R223': self._validate_path_resolution,
            'R224': self._validate_receipts_validation,
            'R225': self._validate_evidence_watermarks,
            'R226': self._validate_rfc_fallback,
            'R227': self._validate_observability_partitions,
            'R228': self._validate_laptop_receipts_partitioning
        }
        
        # Allowed planes and paths from specification
        self.allowed_planes = ['ide', 'tenant', 'product', 'shared']
        
        # Kebab-case pattern
        self.kebab_case_pattern = re.compile(r'^[a-z0-9-]+$')
        
        # Date partition pattern (dt=YYYY-MM-DD)
        self.date_partition_pattern = re.compile(r'dt=\d{4}-\d{2}-\d{2}')
        
        # YYYY/MM pattern for laptop receipts
        self.yyyy_mm_pattern = re.compile(r'\d{4}/\d{2}')
        
        # RFC fallback pattern
        self.rfc_pattern = re.compile(r'UNCLASSIFIED__[a-z0-9-]+')
        
        # Secret patterns (common indicators)
        self.secret_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'api[_-]?key\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']+["\']',
            r'private[_-]?key\s*=\s*["\'][^"\']+["\']',
            r'credentials\s*=\s*["\'][^"\']+["\']',
        ]
        
        # PII patterns
        self.pii_patterns = [
            r'ssn\s*=\s*["\'][^"\']+["\']',
            r'social[_-]?security',
            r'credit[_-]?card',
            r'email\s*=\s*["\'][a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}["\']',
        ]
    
    def validate(self, file_path: str, content: str) -> List[Violation]:
        """Validate storage governance compliance for a file."""
        violations = []
        
        # Run all validation checks
        violations.extend(self._validate_name_casing(content, file_path))
        violations.extend(self._validate_no_code_pii(content, file_path))
        violations.extend(self._validate_no_secrets(content, file_path))
        violations.extend(self._validate_jsonl_receipts(content, file_path))
        violations.extend(self._validate_time_partitions(content, file_path))
        violations.extend(self._validate_policy_signatures(content, file_path))
        violations.extend(self._validate_dual_storage(content, file_path))
        violations.extend(self._validate_path_resolution(content, file_path))
        violations.extend(self._validate_receipts_validation(content, file_path))
        violations.extend(self._validate_evidence_watermarks(content, file_path))
        violations.extend(self._validate_rfc_fallback(content, file_path))
        violations.extend(self._validate_observability_partitions(content, file_path))
        violations.extend(self._validate_laptop_receipts_partitioning(content, file_path))
        
        return violations
    
    def _validate_name_casing(self, content: str, file_path: str) -> List[Violation]:
        """Rule 216: Validate kebab-case naming convention (only [a-z0-9-])."""
        violations = []
        
        # Check for folder/path references in code
        path_patterns = [
            r'["\']([a-zA-Z0-9_/-]+)["\']',  # Quoted paths
            r'Path\(["\']([^"\']+)["\']\)',  # Path constructor
            r'join\([^,]+,\s*["\']([^"\']+)["\']\)',  # path.join
        ]
        
        for pattern in path_patterns:
            for match in re.finditer(pattern, content):
                path_segment = match.group(1)
                # Skip URLs and absolute paths
                if '://' in path_segment or path_segment.startswith('/'):
                    continue
                
                # Extract folder names from path
                parts = path_segment.split('/')
                for part in parts:
                    if part and not part.startswith('.'):
                        # Check if it violates kebab-case (contains uppercase or underscore)
                        if re.search(r'[A-Z_]', part):
                            violations.append(Violation(
                                rule_id='R216',
                                rule_name='Name casing & charset: kebab-case [a-z0-9-] only',
                                rule_number=216,
                                severity=Severity.ERROR,
                                message=f'Folder name "{part}" violates kebab-case rule. Use only lowercase letters, numbers, and hyphens.',
                                file_path=file_path,
                                line_number=content[:match.start()].count('\n') + 1,
                                column_number=match.start() - content.rfind('\n', 0, match.start()) - 1,
                                code_snippet=match.group(0),
                                fix_suggestion=f'Change to kebab-case: {part.lower().replace("_", "-")}',
                                category='storage_governance'
                            ))
        
        return violations
    
    def _validate_no_code_pii(self, content: str, file_path: str) -> List[Violation]:
        """Rule 217: Validate no source code or PII in storage paths."""
        violations = []
        
        # Check if file appears to be storing code in data paths
        storage_indicators = ['storage/', '/data/', '/evidence/', '/receipts/']
        
        for indicator in storage_indicators:
            if indicator in file_path or indicator in content:
                # Check for code patterns being written to storage
                code_patterns = [
                    r'\.write\([^)]*\b(def|class|import|function)\b',
                    r'\.save\([^)]*\b(def|class|import|function)\b',
                    r'\.store\([^)]*\b(def|class|import|function)\b',
                    r'data\s*=\s*["\']\s*def\s+\w+\s*\(',
                ]
                
                for pattern in code_patterns:
                    for match in re.finditer(pattern, content, re.IGNORECASE):
                        violations.append(Violation(
                            rule_id='R217',
                            rule_name='No source code/PII in stores',
                            rule_number=217,
                            severity=Severity.ERROR,
                            message='Source code detected in storage operation. Storage must not contain code or PII.',
                            file_path=file_path,
                            line_number=content[:match.start()].count('\n') + 1,
                            column_number=match.start() - content.rfind('\n', 0, match.start()) - 1,
                            code_snippet=match.group(0)[:100],
                            fix_suggestion='Store only handles, IDs, and metadata. Never store source code.',
                            category='storage_governance'
                        ))
                
                # Check for PII patterns
                for pattern in self.pii_patterns:
                    for match in re.finditer(pattern, content, re.IGNORECASE):
                        violations.append(Violation(
                            rule_id='R217',
                            rule_name='No source code/PII in stores',
                            rule_number=217,
                            severity=Severity.ERROR,
                            message='PII detected in storage operation. Storage must not contain personally identifiable information.',
                            file_path=file_path,
                            line_number=content[:match.start()].count('\n') + 1,
                            column_number=match.start() - content.rfind('\n', 0, match.start()) - 1,
                            code_snippet=match.group(0),
                            fix_suggestion='Use handles or IDs instead of PII. Redact sensitive information.',
                            category='storage_governance'
                        ))
        
        return violations
    
    def _validate_no_secrets(self, content: str, file_path: str) -> List[Violation]:
        """Rule 218: Validate no secrets or private keys on disk."""
        violations = []
        
        # Check for hardcoded secrets
        for pattern in self.secret_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                violations.append(Violation(
                    rule_id='R218',
                    rule_name='No secrets/private keys on disk',
                    rule_number=218,
                    severity=Severity.ERROR,
                    message='Hardcoded secret detected. Never store secrets or private keys on disk.',
                    file_path=file_path,
                    line_number=content[:match.start()].count('\n') + 1,
                    column_number=match.start() - content.rfind('\n', 0, match.start()) - 1,
                    code_snippet=match.group(0),
                    fix_suggestion='Use secrets manager, HSM, or KMS. Load secrets from environment variables.',
                    category='storage_governance'
                ))
        
        # Check for private key file operations
        private_key_patterns = [
            r'\.pem["\']',
            r'\.key["\']',
            r'private[_-]key',
            r'\.p12["\']',
            r'\.pfx["\']',
        ]
        
        for pattern in private_key_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                # Check if it's being written/saved
                context = content[max(0, match.start()-50):match.end()+50]
                if any(op in context.lower() for op in ['write', 'save', 'store', 'open(']):
                    violations.append(Violation(
                        rule_id='R218',
                        rule_name='No secrets/private keys on disk',
                        rule_number=218,
                        severity=Severity.ERROR,
                        message='Private key file operation detected. Private keys should not be stored on disk.',
                        file_path=file_path,
                        line_number=content[:match.start()].count('\n') + 1,
                        column_number=match.start() - content.rfind('\n', 0, match.start()) - 1,
                        code_snippet=match.group(0),
                        fix_suggestion='Store only public keys in trust/pubkeys/. Use HSM or KMS for private keys.',
                        category='storage_governance'
                    ))
        
        return violations
    
    def _validate_jsonl_receipts(self, content: str, file_path: str) -> List[Violation]:
        """Rule 219: Validate JSONL receipts format (newline-delimited, signed, append-only)."""
        violations = []
        
        # Check for receipt handling
        if 'receipt' in content.lower():
            # Check for proper JSONL format
            if '.json' in content and 'receipt' in content.lower():
                # Look for operations that should be JSONL
                jsonl_violations = [
                    (r'json\.dump\(', 'Use JSONL format (newline-delimited) for receipts, not single JSON'),
                    (r'json\.dumps\([^)]+\)(?!\s*\+\s*["\']\\n)', 'JSONL requires newline after each record'),
                ]
                
                for pattern, message in jsonl_violations:
                    for match in re.finditer(pattern, content):
                        context = content[match.start():min(match.end()+100, len(content))]
                        if 'receipt' in context.lower():
                            violations.append(Violation(
                                rule_id='R219',
                                rule_name='JSONL receipts (newline-delimited, signed, append-only)',
                                rule_number=219,
                                severity=Severity.WARNING,
                                message=message,
                                file_path=file_path,
                                line_number=content[:match.start()].count('\n') + 1,
                                column_number=match.start() - content.rfind('\n', 0, match.start()) - 1,
                                code_snippet=match.group(0),
                                fix_suggestion='Use JSONL format: one JSON object per line, each line signed.',
                                category='storage_governance'
                            ))
            
            # Check for append-only pattern
            write_patterns = [
                (r'\.write\([\'"]w[\'"]', 'Receipts must be append-only. Use "a" mode, not "w"'),
                (r'truncate\(', 'Receipts are append-only. Never truncate receipt files'),
                (r'\.seek\(0\)', 'Receipts are append-only. Do not overwrite existing receipts'),
            ]
            
            for pattern, message in write_patterns:
                for match in re.finditer(pattern, content):
                    context = content[max(0, match.start()-100):min(match.end()+100, len(content))]
                    if 'receipt' in context.lower():
                        violations.append(Violation(
                            rule_id='R219',
                            rule_name='JSONL receipts (newline-delimited, signed, append-only)',
                            rule_number=219,
                            severity=Severity.ERROR,
                            message=message,
                            file_path=file_path,
                            line_number=content[:match.start()].count('\n') + 1,
                            column_number=match.start() - content.rfind('\n', 0, match.start()) - 1,
                            code_snippet=match.group(0),
                            fix_suggestion='Use append mode ("a") and never modify existing receipt entries.',
                            category='storage_governance'
                        ))

            # Detect explicit write("w") to receipt files
            for match in re.finditer(r"open\([^)]*receipt[^)]*,\s*['\"]w['\"]\)", content, re.IGNORECASE):
                violations.append(Violation(
                    rule_id='R219',
                    rule_name='JSONL receipts must be append-only',
                    rule_number=219,
                    severity=Severity.ERROR,
                    message='Receipts must be append-only. Use mode "a", not "w".',
                    file_path=file_path,
                    line_number=content[:match.start()].count('\n') + 1,
                    column_number=0,
                    code_snippet=match.group(0),
                    category='storage_governance'
                ))
        
        return violations
    
    def _validate_time_partitions(self, content: str, file_path: str) -> List[Violation]:
        """Rule 220: Validate UTC time partitions (dt=YYYY-MM-DD format)."""
        violations = []
        
        # Look for partition creation or references
        partition_patterns = [
            r'dt=\d{4}-\d{2}-\d{2}',  # Valid format
            r'dt=\d{8}',  # Invalid YYYYMMDD format
            r'dt=\d{2}-\d{2}-\d{4}',  # Invalid MM-DD-YYYY format
            r'date=\d{4}-\d{2}-\d{2}',  # Should be dt= not date=
        ]
        
        # Check for invalid partition formats
        for match in re.finditer(r'dt=[^/\s]+', content):
            partition = match.group(0)
            if not self.date_partition_pattern.match(partition):
                violations.append(Violation(
                    rule_id='R220',
                    rule_name='Time partitions use UTC (dt=YYYY-MM-DD)',
                    rule_number=220,
                    severity=Severity.ERROR,
                    message=f'Invalid time partition format: {partition}. Must use dt=YYYY-MM-DD in UTC.',
                    file_path=file_path,
                    line_number=content[:match.start()].count('\n') + 1,
                    column_number=match.start() - content.rfind('\n', 0, match.start()) - 1,
                    code_snippet=match.group(0),
                    fix_suggestion='Use UTC format: dt=YYYY-MM-DD (e.g., dt=2025-10-20)',
                    category='storage_governance'
                ))
        
        # Check for date= instead of dt=
        for match in re.finditer(r'date=\d{4}-\d{2}-\d{2}', content):
            violations.append(Violation(
                rule_id='R220',
                rule_name='Time partitions use UTC (dt=YYYY-MM-DD)',
                rule_number=220,
                severity=Severity.WARNING,
                message='Use "dt=" prefix for time partitions, not "date="',
                file_path=file_path,
                line_number=content[:match.start()].count('\n') + 1,
                column_number=match.start() - content.rfind('\n', 0, match.start()) - 1,
                code_snippet=match.group(0),
                fix_suggestion='Change "date=" to "dt=" for partition naming',
                category='storage_governance'
            ))
        
        return violations
    
    def _validate_policy_signatures(self, content: str, file_path: str) -> List[Violation]:
        """Rule 221: Validate policy snapshots are signed."""
        violations = []
        
        # Check for policy operations
        if 'policy' in content.lower() and ('snapshot' in content.lower() or 'save' in content.lower()):
            # Look for signature verification
            signature_indicators = ['sign', 'signature', 'verify', 'hash', 'hmac']
            
            # Find policy save/write operations
            policy_operations = list(re.finditer(r'(save|write|store).*policy', content, re.IGNORECASE))
            
            for match in policy_operations:
                # Check if signature is present in context
                context_start = max(0, match.start() - 200)
                context_end = min(len(content), match.end() + 200)
                context = content[context_start:context_end]
                
                has_signature = any(indicator in context.lower() for indicator in signature_indicators)
                
                if not has_signature:
                        violations.append(Violation(
                            rule_id='R221',
                            rule_name='Policy snapshots must be signed',
                            rule_number=221,
                        severity=Severity.ERROR,
                        message='Policy snapshot operation without signature detected. All policy snapshots must be signed.',
                        file_path=file_path,
                        line_number=content[:match.start()].count('\n') + 1,
                        column_number=match.start() - content.rfind('\n', 0, match.start()) - 1,
                        code_snippet=match.group(0),
                        fix_suggestion='Add signature generation and verification for policy snapshots.',
                        category='storage_governance'
                    ))
        
        return violations
    
    def _validate_dual_storage(self, content: str, file_path: str) -> List[Violation]:
        """Rule 222: Validate dual storage compliance (JSONL authority, DB mirrors)."""
        violations = []
        
        # Check for storage operations that should follow dual storage pattern
        dual_storage_keywords = ['evidence', 'receipt', 'audit']
        
        for keyword in dual_storage_keywords:
            if keyword in content.lower():
                # Look for database operations
                db_patterns = ['INSERT', 'UPDATE', 'DELETE', 'execute(', 'cursor.']
                has_db = any(pattern in content for pattern in db_patterns)
                
                # Look for JSONL file operations
                jsonl_patterns = ['.jsonl', 'append(', 'write(']
                has_jsonl = any(pattern in content for pattern in jsonl_patterns)
                
                # If it has DB but no JSONL, warn about dual storage
                if has_db and not has_jsonl:
                    # Find first DB operation
                    for pattern in db_patterns:
                        match = re.search(pattern, content)
                        if match:
                            violations.append(Violation(
                                rule_id='R222',
                                rule_name='Dual storage compliance (JSONL authority, DB mirrors)',
                                rule_number=222,
                                severity=Severity.WARNING,
                                message=f'Database operation for {keyword} without JSONL authority. JSONL is the source of truth, DB mirrors for queries.',
                                file_path=file_path,
                                line_number=content[:match.start()].count('\n') + 1,
                                column_number=match.start() - content.rfind('\n', 0, match.start()) - 1,
                                code_snippet=match.group(0),
                                fix_suggestion='Write to JSONL first (authority), then mirror to DB for indexing/queries.',
                                category='storage_governance'
                            ))
                            break
        
        return violations
    
    def _validate_path_resolution(self, content: str, file_path: str) -> List[Violation]:
        """Rule 223: Validate path resolution via ZU_ROOT environment variable."""
        violations = []
        
        # Check for hardcoded storage paths
        hardcoded_patterns = [
            r'["\'][A-Z]:\\[^"\']*\\(ide|tenant|product|shared)',  # Windows absolute paths
            r'["\']/home/[^"\']*/(ide|tenant|product|shared)',  # Unix absolute paths
            r'["\']D:\\ZeroUI',  # Specific hardcoded path
        ]
        
        for pattern in hardcoded_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                # Check if ZU_ROOT is NOT present nearby
                context = content[max(0, match.start()-100):min(match.end()+100, len(content))]
                if 'ZU_ROOT' not in context and 'os.environ' not in context:
                    violations.append(Violation(
                        rule_id='R223',
                        rule_name='Path resolution via ZU_ROOT environment variable',
                        rule_number=223,
                        severity=Severity.ERROR,
                        message='Hardcoded storage path detected. All paths must be resolved via ZU_ROOT environment variable.',
                        file_path=file_path,
                        line_number=content[:match.start()].count('\n') + 1,
                        column_number=match.start() - content.rfind('\n', 0, match.start()) - 1,
                        code_snippet=match.group(0),
                        fix_suggestion='Use os.environ.get("ZU_ROOT") or config/paths.json for path resolution.',
                        category='storage_governance'
                    ))
        
        return violations
    
    def _validate_receipts_validation(self, content: str, file_path: str) -> List[Violation]:
        """Rule 224: Validate receipts (signed, append-only, no code/PII)."""
        violations = []
        
        # This combines checks from rules 217, 218, 219 specifically for receipts
        if 'receipt' in file_path.lower() or 'receipts/' in content.lower():
            # Check for signature validation in receipt reading
            if 'read' in content.lower() or 'load' in content.lower():
                read_operations = list(re.finditer(r'(read|load|open)\([^)]*receipt', content, re.IGNORECASE))
                
                for match in read_operations:
                    context = content[match.start():min(match.end()+300, len(content))]
                    
                    # Check for signature verification
                    if not any(term in context.lower() for term in ['verify', 'signature', 'check', 'validate']):
                        violations.append(Violation(
                            rule_id='R224',
                            rule_name='Receipts validation (signed, append-only, no code/PII)',
                            rule_number=224,
                            severity=Severity.WARNING,
                            message='Receipt read operation without signature verification. All receipts must be verified.',
                            file_path=file_path,
                            line_number=content[:match.start()].count('\n') + 1,
                            column_number=match.start() - content.rfind('\n', 0, match.start()) - 1,
                            code_snippet=match.group(0),
                            fix_suggestion='Add signature verification when reading receipts.',
                            category='storage_governance'
                        ))
        
        return violations
    
    def _validate_evidence_watermarks(self, content: str, file_path: str) -> List[Violation]:
        """Rule 225: Validate evidence watermarks per-consumer structure."""
        violations = []
        
        # Check for watermark operations
        if 'watermark' in content.lower():
            # Look for consumer-specific structure
            watermark_patterns = [
                r'watermarks/\{?[a-zA-Z_-]+\}?',  # Should have consumer-id
                r'watermarks/["\']',  # Direct path without consumer
            ]
            
            for match in re.finditer(r'watermarks?/', content, re.IGNORECASE):
                # Check if followed by consumer-id segment
                context = content[match.end():min(match.end()+200, len(content))]
                # Extract next path token after watermarks/
                m = re.match(r'([A-Za-z0-9_-]+|\{[^}]+\})/?', context)
                token = m.group(1) if m else ""
                has_consumer = False
                if token:
                    # token is either {consumer-id} or a slug
                    if token.startswith('{') and token.endswith('}'):
                        has_consumer = True
                    elif re.match(r'^[a-z][a-z0-9-]*$', token):
                        has_consumer = True
                if not has_consumer:
                        violations.append(Violation(
                            rule_id='R225',
                        rule_name='Evidence watermarks per-consumer structure',
                            rule_number=225,
                        severity=Severity.WARNING,
                        message='Watermark path should include consumer-id: .../watermarks/{consumer-id}/',
                        file_path=file_path,
                        line_number=content[:match.start()].count('\n') + 1,
                        column_number=match.start() - content.rfind('\n', 0, match.start()) - 1,
                        code_snippet=match.group(0) + context[:30],
                        fix_suggestion='Include consumer-id in watermark path: watermarks/{consumer-id}/',
                        category='storage_governance'
                    ))
        
        return violations
    
    def _validate_rfc_fallback(self, content: str, file_path: str) -> List[Violation]:
        """Rule 226: Validate RFC fallback pattern (UNCLASSIFIED__slug, 24h resolution)."""
        violations = []
        
        # Check for unclassified/fallback handling
        if 'unclassified' in content.lower() or 'fallback' in content.lower():
            # Look for RFC pattern usage
            unclassified_refs = list(re.finditer(r'unclassified', content, re.IGNORECASE))
            
            for match in unclassified_refs:
                # Check if using proper UNCLASSIFIED__ prefix
                context = content[max(0, match.start()-20):min(match.end()+50, len(content))]
                
                # Should match UNCLASSIFIED__slug pattern
                if 'UNCLASSIFIED' in context and not self.rfc_pattern.search(context):
                    violations.append(Violation(
                        rule_id='R229',
                        rule_name='RFC fallback pattern (UNCLASSIFIED__slug, 24h resolution)',
                        rule_number=229,
                        severity=Severity.WARNING,
                        message='Use RFC fallback pattern: UNCLASSIFIED__<slug> (kebab-case slug)',
                        file_path=file_path,
                        line_number=content[:match.start()].count('\n') + 1,
                        column_number=match.start() - content.rfind('\n', 0, match.start()) - 1,
                        code_snippet=context.strip(),
                        fix_suggestion='Use pattern: UNCLASSIFIED__<slug> and resolve within 24h via RFC',
                        category='storage_governance'
                    ))
                
                # Check for 24h resolution mention
                if 'hour' not in context.lower() and 'day' not in context.lower() and '24' not in context:
                    violations.append(Violation(
                        rule_id='R229',
                        rule_name='RFC fallback pattern (UNCLASSIFIED__slug, 24h resolution)',
                        rule_number=229,
                        severity=Severity.INFO,
                        message='Unclassified data must be resolved within 24 hours via RFC process.',
                        file_path=file_path,
                        line_number=content[:match.start()].count('\n') + 1,
                        column_number=match.start() - content.rfind('\n', 0, match.start()) - 1,
                        code_snippet=match.group(0),
                        fix_suggestion='Document 24-hour RFC resolution requirement for unclassified data.',
                        category='storage_governance'
                    ))
        
        return violations
    
    def _validate_observability_partitions(self, content: str, file_path: str) -> List[Violation]:
        """Rule 227: Validate Observability/Adapters use dt= partitions."""
        violations = []
        
        # Check for observability and adapter paths
        partition_required_paths = ['observability/', 'adapters/', 'gateway-logs/', 'reporting/']
        
        for path_type in partition_required_paths:
            if path_type in content.lower():
                # Find references to these paths
                for match in re.finditer(rf'{path_type}[^/\s]*', content, re.IGNORECASE):
                    full_path_match = re.search(rf'{path_type}[^\s\'"]*', content[match.start():min(match.end()+100, len(content))], re.IGNORECASE)
                    
                    if full_path_match:
                        full_path = full_path_match.group(0)
                        
                        # Check if dt= partition is present
                        if 'dt=' not in full_path:
                            violations.append(Violation(
                            rule_id='R227',
                                rule_name='Observability/Adapters use dt= partitions',
                            rule_number=227,
                                severity=Severity.WARNING,
                                message=f'{path_type.strip("/")} path should include dt= partition for time-series data.',
                                file_path=file_path,
                                line_number=content[:match.start()].count('\n') + 1,
                                column_number=match.start() - content.rfind('\n', 0, match.start()) - 1,
                                code_snippet=full_path[:100],
                                fix_suggestion=f'Add dt=YYYY-MM-DD partition: {path_type}metrics/dt=2025-10-20/',
                                category='storage_governance'
                            ))
        
        return violations
    
    def _validate_laptop_receipts_partitioning(self, content: str, file_path: str) -> List[Violation]:
        """Rule 228: Validate laptop receipts use YYYY/MM partitioning."""
        violations = []
        
        # Check for IDE/laptop receipt paths
        laptop_paths = ['ide/agent/receipts/', 'agent/receipts/', '/receipts/']
        
        for laptop_path in laptop_paths:
            if laptop_path in content.lower():
                # Find receipt path references
                for match in re.finditer(rf'{laptop_path}[^\s\'"]*', content, re.IGNORECASE):
                    path = match.group(0)
                    
                    # Check if it has YYYY/MM partition
                    if not self.yyyy_mm_pattern.search(path):
                        violations.append(Violation(
                            rule_id='R228',
                            rule_name='Laptop receipts use YYYY/MM partitioning',
                            rule_number=228,
                            severity=Severity.WARNING,
                            message='Laptop receipts should use month partitioning: receipts/{repo-id}/{YYYY}/{MM}/',
                            file_path=file_path,
                            line_number=content[:match.start()].count('\n') + 1,
                            column_number=match.start() - content.rfind('\n', 0, match.start()) - 1,
                            code_snippet=path[:100],
                            fix_suggestion='Use YYYY/MM partitioning: agent/receipts/repo-id/2025/10/',
                            category='storage_governance'
                        ))
        
        return violations

    def validate_all(self, tree, content: str, file_path: str) -> List[Violation]:
        """
        Validate all storage governance rules.
        
        Args:
            tree: AST tree of the code (not used for storage governance)
            content: File content
            file_path: Path to the file
            
        Returns:
            List of all violations found
        """
        violations = []
        
        # Run all storage governance validations
        for rule_id, validator_func in self.rules.items():
            try:
                rule_violations = validator_func(content, file_path)
                violations.extend(rule_violations)
            except Exception as e:
                # Create error violation for failed rule
                violations.append(Violation(
                    rule_id=rule_id,
                    severity=Severity.ERROR,
                    message=f"Storage governance rule {rule_id} failed to execute: {str(e)}",
                    file_path=file_path,
                    line_number=1,
                    column_number=0,
                    code_snippet="",
                    fix_suggestion="Check storage governance rule implementation",
                    category='storage_governance'
                ))
        
        return violations

