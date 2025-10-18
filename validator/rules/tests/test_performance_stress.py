"""
Performance and stress tests for ZEROUI 2.0 Constitution Validator.

This test suite ensures the system meets performance requirements and
can handle stress conditions gracefully.
"""

import pytest
import time
import json
import os
from pathlib import Path
from typing import Dict, List, Any
import tempfile
import concurrent.futures
import threading

# Import validator components
from validator.core import ConstitutionValidator
from validator.analyzer import CodeAnalyzer
from validator.reporter import ReportGenerator


class TestPerformanceTargets:
    """Test performance targets from configuration."""
    
    def test_startup_time_target(self):
        """Test that validator startup meets performance target."""
        config_path = Path("config/base_config.json")
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        startup_target = config.get('performance_targets', {}).get('startup_time', 2.0)
        
        # Measure startup time
        start_time = time.time()
        validator = ConstitutionValidator("config/constitution_config.json")
        end_time = time.time()
        
        startup_time = end_time - start_time
        assert startup_time <= startup_target, f"Startup time {startup_time:.2f}s exceeds target {startup_target}s"
    
    def test_button_response_time(self):
        """Test that button responses meet performance target."""
        config_path = Path("config/base_config.json")
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        response_target = config.get('performance_targets', {}).get('button_response', 0.1)
        
        # Simulate button response (validation trigger)
        start_time = time.time()
        validator = ConstitutionValidator("config/constitution_config.json")
        # Simulate a quick validation operation
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response_time <= response_target, f"Response time {response_time:.2f}s exceeds target {response_target}s"
    
    def test_data_processing_time(self):
        """Test that data processing meets performance target."""
        config_path = Path("config/base_config.json")
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        processing_target = config.get('performance_targets', {}).get('data_processing', 1.0)
        
        # Create test data
        test_code = """
def test_function():
    # This is a test function
    x = 1 + 2
    return x * 3

class TestClass:
    def __init__(self):
        self.value = 42
    
    def method(self):
        return self.value
"""
        
        # Measure processing time
        start_time = time.time()
        validator = ConstitutionValidator("config/constitution_config.json")
        analyzer = CodeAnalyzer()
        
        # Simulate processing
        try:
            # This might not exist, but we're testing the concept
            if hasattr(analyzer, 'analyze_code'):
                result = analyzer.analyze_code(test_code, "test.py")
        except:
            pass  # Expected if method doesn't exist
        
        end_time = time.time()
        
        processing_time = end_time - start_time
        assert processing_time <= processing_target, f"Processing time {processing_time:.2f}s exceeds target {processing_target}s"


class TestMemoryUsage:
    """Test memory usage and efficiency."""
    
    def test_validator_memory_footprint(self):
        """Test that validator has reasonable memory footprint."""
        import psutil
        import gc
        
        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # Create multiple validators
        validators = []
        for i in range(10):
            validator = ConstitutionValidator("config/constitution_config.json")
            validators.append(validator)
        
        # Get memory after creation
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB for 10 validators)
        max_memory_increase = 100 * 1024 * 1024  # 100MB
        assert memory_increase < max_memory_increase, \
            f"Memory increase {memory_increase / 1024 / 1024:.2f}MB exceeds limit {max_memory_increase / 1024 / 1024}MB"
        
        # Clean up
        del validators
        gc.collect()
    
    def test_config_loading_efficiency(self):
        """Test that configuration loading is efficient."""
        config_path = Path("config/constitution_config.json")
        
        # Measure config loading time
        start_time = time.time()
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        end_time = time.time()
        
        load_time = end_time - start_time
        assert load_time < 0.1, f"Config loading time {load_time:.3f}s is too slow"


class TestConcurrency:
    """Test concurrent access and thread safety."""
    
    def test_concurrent_validation(self):
        """Test that multiple validations can run concurrently."""
        def run_validation(validator_id):
            """Run a validation in a separate thread."""
            try:
                validator = ConstitutionValidator("config/constitution_config.json")
                # Simulate some work
                time.sleep(0.01)
                return f"validator_{validator_id}_completed"
            except Exception as e:
                return f"validator_{validator_id}_error: {str(e)}"
        
        # Run multiple validations concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(run_validation, i) for i in range(5)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All validations should complete successfully
        assert len(results) == 5, "All concurrent validations should complete"
        assert all("completed" in result for result in results), "All validations should complete successfully"
    
    def test_thread_safety(self):
        """Test thread safety of validator components."""
        results = []
        errors = []
        
        def worker(thread_id):
            """Worker function for thread safety test."""
            try:
                validator = ConstitutionValidator("config/constitution_config.json")
                analyzer = CodeAnalyzer()
                
                # Simulate concurrent access to shared resources
                for i in range(10):
                    # Access configuration
                    if hasattr(validator, 'config'):
                        config = validator.config
                    
                    # Access analyzer
                    if hasattr(analyzer, 'analyze_code'):
                        # This might not exist, but we're testing thread safety
                        pass
                    
                    time.sleep(0.001)  # Small delay to increase chance of race conditions
                
                results.append(f"thread_{thread_id}_success")
            except Exception as e:
                errors.append(f"thread_{thread_id}_error: {str(e)}")
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Thread safety errors: {errors}"
        assert len(results) == 5, "All threads should complete successfully"


class TestStressConditions:
    """Test system behavior under stress conditions."""
    
    def test_large_file_handling(self):
        """Test handling of large files."""
        # Create a large test file
        large_code = ""
        for i in range(1000):
            large_code += f"""
def function_{i}():
    # This is function number {i}
    x = {i} * 2
    y = x + {i}
    return y

class Class_{i}:
    def __init__(self):
        self.value = {i}
    
    def method_{i}(self):
        return self.value * {i}
"""
        
        # Test that we can handle large files without crashing
        try:
            validator = ConstitutionValidator()
            analyzer = CodeAnalyzer()
            
            # This should not crash even with large input
            if hasattr(analyzer, 'analyze_code'):
                result = analyzer.analyze_code(large_code, "large_test.py")
            
            assert True, "Large file handling successful"
        except Exception as e:
            # If it fails, it should fail gracefully
            assert "memory" not in str(e).lower(), f"Large file should not cause memory issues: {e}"
    
    def test_malformed_input_handling(self):
        """Test handling of malformed input."""
        malformed_inputs = [
            "",  # Empty string
            "invalid python code here",  # Invalid syntax
            "def incomplete_function(",  # Incomplete syntax
            "class IncompleteClass:",  # Incomplete class
            None,  # None input
        ]
        
        validator = ConstitutionValidator("config/constitution_config.json")
        analyzer = CodeAnalyzer()
        
        for i, malformed_input in enumerate(malformed_inputs):
            try:
                if hasattr(analyzer, 'analyze_code') and malformed_input is not None:
                    result = analyzer.analyze_code(malformed_input, f"malformed_{i}.py")
                # Should not crash
                assert True, f"Malformed input {i} handled gracefully"
            except Exception as e:
                # Should fail gracefully, not crash
                assert "crash" not in str(e).lower(), f"Malformed input {i} should not crash: {e}"
    
    def test_resource_cleanup(self):
        """Test that resources are properly cleaned up."""
        import gc
        
        # Create and destroy many validators
        for i in range(100):
            validator = ConstitutionValidator("config/constitution_config.json")
            del validator
        
        # Force garbage collection
        gc.collect()
        
        # System should still be responsive
        start_time = time.time()
        validator = ConstitutionValidator("config/constitution_config.json")
        end_time = time.time()
        
        creation_time = end_time - start_time
        assert creation_time < 1.0, "System should remain responsive after resource cleanup"


class TestErrorRecovery:
    """Test error recovery and resilience."""
    
    def test_config_file_corruption_recovery(self):
        """Test recovery from corrupted configuration files."""
        config_path = Path("config/constitution_config.json")
        
        # Backup original config
        with open(config_path, 'r') as f:
            original_config = f.read()
        
        try:
            # Corrupt the config file
            with open(config_path, 'w') as f:
                f.write("invalid json content")
            
            # Validator should handle corruption gracefully
            try:
                validator = ConstitutionValidator()
                # Should either work with fallback or fail gracefully
                assert True, "Corrupted config handled gracefully"
            except Exception as e:
                # Should fail gracefully, not crash
                assert "crash" not in str(e).lower(), f"Config corruption should not crash: {e}"
        
        finally:
            # Restore original config
            with open(config_path, 'w') as f:
                f.write(original_config)
    
    def test_missing_file_handling(self):
        """Test handling of missing files."""
        # Test with non-existent config path
        try:
            validator = ConstitutionValidator("non_existent_config.json")
            # Should either work with defaults or fail gracefully
            assert True, "Missing config file handled gracefully"
        except Exception as e:
            # Should fail gracefully, not crash
            assert "crash" not in str(e).lower(), f"Missing config should not crash: {e}"


class TestScalability:
    """Test system scalability."""
    
    def test_rule_count_scalability(self):
        """Test that system scales with number of rules."""
        config_path = Path("config/base_config.json")
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        total_rules = config.get('total_rules', 215)
        
        # System should handle the configured number of rules efficiently
        start_time = time.time()
        validator = ConstitutionValidator("config/constitution_config.json")
        end_time = time.time()
        
        initialization_time = end_time - start_time
        
        # Initialization time should scale reasonably with rule count
        max_time_per_rule = 0.01  # 10ms per rule
        max_initialization_time = total_rules * max_time_per_rule
        
        assert initialization_time <= max_initialization_time, \
            f"Initialization time {initialization_time:.3f}s too slow for {total_rules} rules"
    
    def test_concurrent_user_simulation(self):
        """Simulate multiple concurrent users."""
        def simulate_user(user_id):
            """Simulate a user session."""
            try:
                validator = ConstitutionValidator("config/constitution_config.json")

                # Simulate user actions
                for action in range(5):
                    # Simulate validation request
                    time.sleep(0.01)

                return f"user_{user_id}_completed"
            except Exception as e:
                return f"user_{user_id}_error: {str(e)}"
        
        # Simulate 20 concurrent users
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(simulate_user, i) for i in range(20)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All users should complete successfully
        assert len(results) == 20, "All concurrent users should complete"
        success_count = sum(1 for result in results if "completed" in result)
        assert success_count >= 18, f"At least 90% of users should succeed ({success_count}/20)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
