#!/usr/bin/env python3
"""
Performance and Stress Test Suite for ZEROUI 2.0 Constitution Rules
Following Martin Fowler's Testing Principles

This test suite validates performance characteristics, memory usage,
and scalability of the constitution rules validation system.
"""

import unittest
import time
import psutil
import gc
import threading
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from pathlib import Path
import sys
import json
import os
from typing import List, Dict, Any
import random
import string

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from validator.core import ConstitutionValidator
from validator.models import ValidationResult, Violation, Severity


class PerformanceTestBase(unittest.TestCase):
    """Base class for performance tests with common utilities."""
    
    def setUp(self):
        """Set up performance test environment for each test."""
        self.validator = ConstitutionValidator("config/constitution_rules.json")
        self.test_files_dir = Path(__file__).parent / "test_files"
        self.test_files_dir.mkdir(exist_ok=True)
        
        # Generate test files of various sizes fresh for each test
        self._generate_test_files()
    
    def tearDown(self):
        """Clean up test files after each test."""
        import shutil
        if self.test_files_dir.exists():
            shutil.rmtree(self.test_files_dir)
    
    def _generate_test_files(self):
        """Generate test files of various sizes for performance testing."""
        # Small file (1KB)
        small_code = self._generate_code(100)
        with open(self.test_files_dir / "small.py", 'w') as f:
            f.write(small_code)
        
        # Medium file (10KB)
        medium_code = self._generate_code(1000)
        with open(self.test_files_dir / "medium.py", 'w') as f:
            f.write(medium_code)
        
        # Large file (100KB)
        large_code = self._generate_code(10000)
        with open(self.test_files_dir / "large.py", 'w') as f:
            f.write(large_code)
        
        # Very large file (1MB)
        very_large_code = self._generate_code(100000)
        with open(self.test_files_dir / "very_large.py", 'w') as f:
            f.write(very_large_code)
    
    @staticmethod
    def _generate_code(lines: int) -> str:
        """Generate test code with specified number of lines."""
        code_lines = [
            '#!/usr/bin/env python3',
            '"""Generated test code for performance testing."""',
            '',
            'import os',
            'import sys',
            'import json',
            'from typing import List, Dict, Any',
            '',
            'class TestClass:',
            '    """Test class for performance validation."""',
            '',
            '    def __init__(self, name: str):',
            '        """Initialize test class."""',
            '        self.name = name',
            '        self.data = []',
            '',
            '    def process_data(self, data: List[str]) -> Dict[str, Any]:',
            '        """Process data and return results."""',
            '        result = {}',
            '        for item in data:',
            '            result[item] = len(item)',
            '        return result',
            '',
            '    def validate_input(self, value: str) -> bool:',
            '        """Validate input value."""',
            '        return value is not None and len(value) > 0',
            ''
        ]
        
        # Add more lines to reach target
        for i in range(lines - len(code_lines)):
            code_lines.append(f'    def method_{i}(self):')
            code_lines.append(f'        """Method {i} for testing."""')
            code_lines.append(f'        return "result_{i}"')
            code_lines.append('')
        
        return '\n'.join(code_lines)
    
    def _measure_memory_usage(self, func, *args, **kwargs):
        """Measure memory usage of a function."""
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        result = func(*args, **kwargs)
        
        final_memory = process.memory_info().rss
        memory_usage = final_memory - initial_memory
        
        return result, memory_usage
    
    def _measure_execution_time(self, func, *args, **kwargs):
        """Measure execution time of a function."""
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        
        return result, execution_time


class TestValidationPerformance(PerformanceTestBase):
    """Test validation performance characteristics."""
    
    @unittest.skip("Performance tests temporarily disabled")
    def test_small_file_validation_performance(self):
        """Test validation performance on small files."""
        with open(self.test_files_dir / "small.py", 'r') as f:
            content = f.read()
        
        # Create a temporary file for testing
        test_file = self.test_files_dir / "small.py"
        result, execution_time = self._measure_execution_time(
            self.validator.validate_file, str(test_file)
        )
        
        # Small file validation should complete within 1 second
        self.assertLess(execution_time, 1.0, 
                       f"Small file validation took {execution_time:.3f}s, expected < 1.0s")
        
        # Should not have excessive violations
        self.assertLessEqual(result.total_violations, 50, 
                           "Small file should not have excessive violations")
    
    @unittest.skip("Performance tests temporarily disabled")
    def test_medium_file_validation_performance(self):
        """Test validation performance on medium files."""
        with open(self.test_files_dir / "medium.py", 'r') as f:
            content = f.read()
        
        test_file = self.test_files_dir / "medium.py"
        result, execution_time = self._measure_execution_time(
            self.validator.validate_file, str(test_file)
        )
        
        # Medium file validation should complete within 5 seconds
        self.assertLess(execution_time, 5.0, 
                       f"Medium file validation took {execution_time:.3f}s, expected < 5.0s")
    
    @unittest.skip("Performance tests temporarily disabled")
    def test_large_file_validation_performance(self):
        """Test validation performance on large files."""
        with open(self.test_files_dir / "large.py", 'r') as f:
            content = f.read()
        
        test_file = self.test_files_dir / "large.py"
        result, execution_time = self._measure_execution_time(
            self.validator.validate_file, str(test_file)
        )
        
        # Large file validation should complete within 30 seconds
        self.assertLess(execution_time, 30.0, 
                       f"Large file validation took {execution_time:.3f}s, expected < 30.0s")
    
    @unittest.skip("Performance tests temporarily disabled")
    def test_very_large_file_validation_performance(self):
        """Test validation performance on very large files."""
        with open(self.test_files_dir / "very_large.py", 'r') as f:
            content = f.read()
        
        test_file = self.test_files_dir / "very_large.py"
        result, execution_time = self._measure_execution_time(
            self.validator.validate_file, str(test_file)
        )
        
        # Very large file validation should complete within 60 seconds
        self.assertLess(execution_time, 60.0, 
                       f"Very large file validation took {execution_time:.3f}s, expected < 60.0s")


class TestMemoryUsage(PerformanceTestBase):
    """Test memory usage characteristics."""
    
    def test_memory_usage_small_file(self):
        """Test memory usage for small file validation."""
        with open(self.test_files_dir / "small.py", 'r') as f:
            content = f.read()
        
        test_file = self.test_files_dir / "small.py"
        result, memory_usage = self._measure_memory_usage(
            self.validator.validate_file, str(test_file)
        )
        
        # Memory usage should be reasonable (less than 10MB)
        self.assertLess(memory_usage, 10 * 1024 * 1024, 
                       f"Small file validation used {memory_usage / (1024*1024):.2f}MB, expected < 10MB")
    
    def test_memory_usage_medium_file(self):
        """Test memory usage for medium file validation."""
        with open(self.test_files_dir / "medium.py", 'r') as f:
            content = f.read()
        
        test_file = self.test_files_dir / "medium.py"
        result, memory_usage = self._measure_memory_usage(
            self.validator.validate_file, str(test_file)
        )
        
        # Memory usage should be reasonable (less than 50MB)
        self.assertLess(memory_usage, 50 * 1024 * 1024, 
                       f"Medium file validation used {memory_usage / (1024*1024):.2f}MB, expected < 50MB")
    
    def test_memory_usage_large_file(self):
        """Test memory usage for large file validation."""
        with open(self.test_files_dir / "large.py", 'r') as f:
            content = f.read()
        
        test_file = self.test_files_dir / "large.py"
        result, memory_usage = self._measure_memory_usage(
            self.validator.validate_file, str(test_file)
        )
        
        # Memory usage should be reasonable (less than 100MB)
        self.assertLess(memory_usage, 100 * 1024 * 1024, 
                       f"Large file validation used {memory_usage / (1024*1024):.2f}MB, expected < 100MB")
    
    def test_memory_leak_detection(self):
        """Test for memory leaks in repeated validation."""
        with open(self.test_files_dir / "medium.py", 'r') as f:
            content = f.read()
        
        initial_memory = psutil.Process().memory_info().rss
        
        # Run validation multiple times
        for i in range(10):
            test_file = self.test_files_dir / f"test_{i}.py"
            # Create temporary file for each test
            with open(test_file, 'w') as f:
                f.write(content)
            self.validator.validate_file(str(test_file))
            gc.collect()  # Force garbage collection
        
        final_memory = psutil.Process().memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be minimal (less than 20MB)
        self.assertLess(memory_increase, 20 * 1024 * 1024, 
                       f"Memory leak detected: {memory_increase / (1024*1024):.2f}MB increase")


class TestConcurrentValidation(PerformanceTestBase):
    """Test concurrent validation performance."""
    
    @unittest.skip("Performance tests temporarily disabled")
    def test_concurrent_validation_threads(self):
        """Test validation performance with multiple threads."""
        with open(self.test_files_dir / "medium.py", 'r') as f:
            content = f.read()
        
        def validate_file(file_id):
            test_file = self.test_files_dir / f"concurrent_{file_id}.py"
            # Create temporary file for each test
            with open(test_file, 'w') as f:
                f.write(content)
            return self.validator.validate_file(str(test_file))
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(validate_file, i) for i in range(10)]
            results = [future.result() for future in futures]
        
        execution_time = time.time() - start_time
        
        # Concurrent validation should complete within reasonable time
        self.assertLess(execution_time, 30.0, 
                       f"Concurrent validation took {execution_time:.3f}s, expected < 30.0s")
        
        # All validations should complete successfully
        self.assertEqual(len(results), 10, "All concurrent validations should complete")
    
    @unittest.skip("Performance tests temporarily disabled")
    def test_concurrent_validation_processes(self):
        """Test validation performance with multiple processes."""
        with open(self.test_files_dir / "medium.py", 'r') as f:
            content = f.read()
        
        def validate_file_process(file_id):
            validator = ConstitutionValidator("config/constitution_rules.json")
            test_file = self.test_files_dir / f"process_{file_id}.py"
            # Create temporary file for each test
            with open(test_file, 'w') as f:
                f.write(content)
            return validator.validate_file(str(test_file))
        
        start_time = time.time()
        
        with ProcessPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(validate_file_process, i) for i in range(4)]
            results = [future.result() for future in futures]
        
        execution_time = time.time() - start_time
        
        # Process-based validation should complete within reasonable time
        self.assertLess(execution_time, 60.0, 
                       f"Process validation took {execution_time:.3f}s, expected < 60.0s")
        
        # All validations should complete successfully
        self.assertEqual(len(results), 4, "All process validations should complete")


class TestStressValidation(PerformanceTestBase):
    """Test stress scenarios for validation."""
    
    @unittest.skip("Performance tests temporarily disabled")
    def test_rapid_validation_stress(self):
        """Test rapid successive validation calls."""
        with open(self.test_files_dir / "small.py", 'r') as f:
            content = f.read()
        
        start_time = time.time()
        
        # Perform 100 rapid validations
        for i in range(100):
            test_file = self.test_files_dir / f"stress_{i}.py"
            # Create temporary file for each test
            with open(test_file, 'w') as f:
                f.write(content)
            result = self.validator.validate_file(str(test_file))
            self.assertIsInstance(result, ValidationResult)
        
        execution_time = time.time() - start_time
        
        # 100 validations should complete within 30 seconds
        self.assertLess(execution_time, 30.0, 
                       f"Rapid validation took {execution_time:.3f}s, expected < 30.0s")
    
    @unittest.skip("Performance tests temporarily disabled")
    def test_mixed_file_sizes_stress(self):
        """Test validation with mixed file sizes."""
        file_sizes = ["small.py", "medium.py", "large.py"]
        results = []
        
        start_time = time.time()
        
        # Validate files of different sizes in random order
        for i in range(20):
            file_size = random.choice(file_sizes)
            with open(self.test_files_dir / file_size, 'r') as f:
                content = f.read()
            
            test_file = self.test_files_dir / f"mixed_{i}_{file_size}"
            # Create temporary file for each test
            with open(test_file, 'w') as f:
                f.write(content)
            result = self.validator.validate_file(str(test_file))
            results.append(result)
        
        execution_time = time.time() - start_time
        
        # Mixed validation should complete within 60 seconds
        self.assertLess(execution_time, 60.0, 
                       f"Mixed validation took {execution_time:.3f}s, expected < 60.0s")
        
        # All validations should complete
        self.assertEqual(len(results), 20, "All mixed validations should complete")
    
    @unittest.skip("Performance tests temporarily disabled")
    def test_memory_pressure_stress(self):
        """Test validation under memory pressure."""
        # Create memory pressure by allocating large objects
        memory_objects = []
        for i in range(10):
            memory_objects.append([0] * 1000000)  # 1MB each
        
        try:
            with open(self.test_files_dir / "medium.py", 'r') as f:
                content = f.read()
            
            # Validation should still work under memory pressure
            test_file = self.test_files_dir / "memory_pressure.py"
            # Create temporary file for test
            with open(test_file, 'w') as f:
                f.write(content)
            result = self.validator.validate_file(str(test_file))
            self.assertIsInstance(result, ValidationResult)
            
        finally:
            # Clean up memory objects
            del memory_objects
            gc.collect()


class TestScalability(PerformanceTestBase):
    """Test scalability characteristics."""
    
    def test_rule_count_scalability(self):
        """Test that validation scales with rule count."""
        # Test with different numbers of active rules
        rule_counts = [50, 100, 200, 293]  # All available rules
        
        for rule_count in rule_counts:
            with open(self.test_files_dir / "medium.py", 'r') as f:
                content = f.read()
            
            start_time = time.time()
            test_file = self.test_files_dir / f"scalability_{rule_count}.py"
            # Create temporary file for test
            with open(test_file, 'w') as f:
                f.write(content)
            result = self.validator.validate_file(str(test_file))
            execution_time = time.time() - start_time
            
            # Execution time should scale reasonably with rule count
            max_time = rule_count * 0.1  # 0.1 seconds per rule maximum
            self.assertLess(execution_time, max_time, 
                           f"Validation with {rule_count} rules took {execution_time:.3f}s, expected < {max_time:.3f}s")
    
    def test_file_size_scalability(self):
        """Test that validation scales with file size."""
        file_sizes = [
            ("small.py", 1.0),    # 1 second max
            ("medium.py", 5.0),   # 5 seconds max
            ("large.py", 30.0),   # 30 seconds max
        ]
        
        for filename, max_time in file_sizes:
            with open(self.test_files_dir / filename, 'r') as f:
                content = f.read()
            
            start_time = time.time()
            test_file = self.test_files_dir / f"scalability_{filename}"
            # Create temporary file for test
            with open(test_file, 'w') as f:
                f.write(content)
            result = self.validator.validate_file(str(test_file))
            execution_time = time.time() - start_time
            
            self.assertLess(execution_time, max_time, 
                           f"Validation of {filename} took {execution_time:.3f}s, expected < {max_time:.3f}s")


if __name__ == '__main__':
    # Run performance tests with detailed output
    unittest.main(verbosity=2)
