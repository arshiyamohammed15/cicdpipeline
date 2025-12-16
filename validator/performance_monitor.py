#!/usr/bin/env python3
"""
Performance monitoring for the validation system.

This module provides detailed performance metrics, profiling, and monitoring
capabilities for the validation system.
"""

import time
import psutil
import threading
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
from contextlib import contextmanager
import json

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """A single performance metric."""
    name: str
    value: float
    unit: str
    timestamp: datetime
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationProfile:
    """Profile of a validation operation."""
    file_path: str
    file_size: int
    line_count: int
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    violations_found: int = 0
    rules_processed: int = 0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    ast_parsing_time: float = 0.0
    rule_processing_time: float = 0.0
    report_generation_time: float = 0.0


class PerformanceMonitor:
    """
    Performance monitor for the validation system.

    This monitor tracks:
    - Validation performance metrics
    - Memory and CPU usage
    - Cache performance
    - Rule processing times
    - System resource utilization
    """

    def __init__(self, max_history: int = 1000):
        """
        Initialize the performance monitor.

        Args:
            max_history: Maximum number of historical records to keep
        """
        self.max_history = max_history
        self.metrics: deque = deque(maxlen=max_history)
        self.profiles: deque = deque(maxlen=max_history)
        self.current_profiles: Dict[str, ValidationProfile] = {}
        self.lock = threading.Lock()

        # Performance counters
        self.counters = defaultdict(int)
        self.timers = defaultdict(list)

        # System monitoring
        self.system_metrics = deque(maxlen=100)
        self._monitoring_thread = None
        self._monitoring_active = False

    def start_monitoring(self, interval: float = 1.0):
        """
        Start system monitoring in a background thread.

        Args:
            interval: Monitoring interval in seconds
        """
        if self._monitoring_active:
            return

        self._monitoring_active = True
        self._monitoring_thread = threading.Thread(
            target=self._monitor_system,
            args=(interval,),
            daemon=True
        )
        self._monitoring_thread.start()

    def stop_monitoring(self):
        """Stop system monitoring."""
        self._monitoring_active = False
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=2.0)

    def _monitor_system(self, interval: float):
        """Monitor system metrics in background thread."""
        while self._monitoring_active:
            try:
                # Get system metrics
                cpu_percent = psutil.cpu_percent()
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')

                system_metric = {
                    'timestamp': datetime.now(),
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_used': memory.used,
                    'memory_available': memory.available,
                    'disk_percent': disk.percent,
                    'disk_used': disk.used,
                    'disk_free': disk.free
                }

                with self.lock:
                    self.system_metrics.append(system_metric)

                time.sleep(interval)
            except Exception as e:
                logger.error(f"Error in system monitoring: {e}", exc_info=True)
                time.sleep(interval)

    @contextmanager
    def profile_validation(self, file_path: str, file_size: int, line_count: int):
        """
        Context manager for profiling validation operations.

        Args:
            file_path: Path to the file being validated
            file_size: Size of the file in bytes
            line_count: Number of lines in the file
        """
        profile = ValidationProfile(
            file_path=file_path,
            file_size=file_size,
            line_count=line_count,
            start_time=datetime.now()
        )

        self.current_profiles[file_path] = profile

        try:
            yield profile
        finally:
            profile.end_time = datetime.now()
            profile.duration = (profile.end_time - profile.start_time).total_seconds()

            with self.lock:
                self.profiles.append(profile)
                if file_path in self.current_profiles:
                    del self.current_profiles[file_path]

    def record_metric(self, name: str, value: float, unit: str = "",
                     context: Dict[str, Any] = None):
        """
        Record a performance metric.

        Args:
            name: Name of the metric
            value: Metric value
            unit: Unit of measurement
            context: Additional context information
        """
        metric = PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            timestamp=datetime.now(),
            context=context or {}
        )

        with self.lock:
            self.metrics.append(metric)

    def increment_counter(self, name: str, value: int = 1):
        """
        Increment a performance counter.

        Args:
            name: Counter name
            value: Value to increment by
        """
        with self.lock:
            self.counters[name] += value

    def record_timing(self, name: str, duration: float):
        """
        Record a timing measurement.

        Args:
            name: Timing name
            duration: Duration in seconds
        """
        with self.lock:
            self.timers[name].append(duration)

    @contextmanager
    def time_operation(self, name: str):
        """
        Context manager for timing operations.

        Args:
            name: Name of the operation
        """
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.record_timing(name, duration)

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a summary of performance metrics."""
        with self.lock:
            summary = {
                'total_validations': len(self.profiles),
                'active_validations': len(self.current_profiles),
                'total_metrics': len(self.metrics),
                'counters': dict(self.counters),
                'timing_stats': {},
                'system_stats': self._get_system_stats(),
                'recent_performance': self._get_recent_performance()
            }

            # Calculate timing statistics
            for name, times in self.timers.items():
                if times:
                    summary['timing_stats'][name] = {
                        'count': len(times),
                        'total': sum(times),
                        'average': sum(times) / len(times),
                        'min': min(times),
                        'max': max(times)
                    }

            return summary

    def _get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics."""
        if not self.system_metrics:
            return {}

        recent_metrics = list(self.system_metrics)[-10:]  # Last 10 measurements

        return {
            'cpu_average': sum(m['cpu_percent'] for m in recent_metrics) / len(recent_metrics),
            'memory_average': sum(m['memory_percent'] for m in recent_metrics) / len(recent_metrics),
            'disk_average': sum(m['disk_percent'] for m in recent_metrics) / len(recent_metrics),
            'last_measurement': recent_metrics[-1] if recent_metrics else None
        }

    def _get_recent_performance(self) -> Dict[str, Any]:
        """Get recent performance statistics."""
        if not self.profiles:
            return {}

        recent_profiles = list(self.profiles)[-10:]  # Last 10 validations

        return {
            'average_duration': sum(p.duration for p in recent_profiles if p.duration) / len(recent_profiles),
            'average_violations': sum(p.violations_found for p in recent_profiles) / len(recent_profiles),
            'average_rules_processed': sum(p.rules_processed for p in recent_profiles) / len(recent_profiles),
            'cache_hit_rate': self._calculate_cache_hit_rate(recent_profiles),
            'files_per_second': len(recent_profiles) / sum(p.duration for p in recent_profiles if p.duration)
        }

    def _calculate_cache_hit_rate(self, profiles: List[ValidationProfile]) -> float:
        """Calculate cache hit rate from profiles."""
        total_hits = sum(p.cache_hits for p in profiles)
        total_misses = sum(p.cache_misses for p in profiles)

        if total_hits + total_misses == 0:
            return 0.0

        return total_hits / (total_hits + total_misses)

    def get_detailed_metrics(self, time_window: timedelta = None) -> List[Dict[str, Any]]:
        """
        Get detailed metrics within a time window.

        Args:
            time_window: Time window to filter metrics

        Returns:
            List of detailed metrics
        """
        with self.lock:
            if time_window:
                cutoff_time = datetime.now() - time_window
                filtered_metrics = [m for m in self.metrics if m.timestamp >= cutoff_time]
            else:
                filtered_metrics = list(self.metrics)

            return [
                {
                    'name': m.name,
                    'value': m.value,
                    'unit': m.unit,
                    'timestamp': m.timestamp.isoformat(),
                    'context': m.context
                }
                for m in filtered_metrics
            ]

    def get_validation_profiles(self, time_window: timedelta = None) -> List[Dict[str, Any]]:
        """
        Get validation profiles within a time window.

        Args:
            time_window: Time window to filter profiles

        Returns:
            List of validation profiles
        """
        with self.lock:
            if time_window:
                cutoff_time = datetime.now() - time_window
                filtered_profiles = [p for p in self.profiles if p.start_time >= cutoff_time]
            else:
                filtered_profiles = list(self.profiles)

            return [
                {
                    'file_path': p.file_path,
                    'file_size': p.file_size,
                    'line_count': p.line_count,
                    'start_time': p.start_time.isoformat(),
                    'end_time': p.end_time.isoformat() if p.end_time else None,
                    'duration': p.duration,
                    'violations_found': p.violations_found,
                    'rules_processed': p.rules_processed,
                    'memory_usage': p.memory_usage,
                    'cpu_usage': p.cpu_usage,
                    'cache_hits': p.cache_hits,
                    'cache_misses': p.cache_misses,
                    'ast_parsing_time': p.ast_parsing_time,
                    'rule_processing_time': p.rule_processing_time,
                    'report_generation_time': p.report_generation_time
                }
                for p in filtered_profiles
            ]

    def export_metrics(self, file_path: str, time_window: timedelta = None):
        """
        Export metrics to a JSON file.

        Args:
            file_path: Path to export file
            time_window: Time window to export
        """
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'summary': self.get_performance_summary(),
            'metrics': self.get_detailed_metrics(time_window),
            'profiles': self.get_validation_profiles(time_window)
        }

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2)

    def clear_metrics(self):
        """Clear all stored metrics."""
        with self.lock:
            self.metrics.clear()
            self.profiles.clear()
            self.current_profiles.clear()
            self.counters.clear()
            self.timers.clear()
            self.system_metrics.clear()

    def get_performance_recommendations(self) -> List[str]:
        """
        Get performance improvement recommendations.

        Returns:
            List of recommendation strings
        """
        recommendations = []
        summary = self.get_performance_summary()

        # Check cache performance
        if 'cache_hit_rate' in summary.get('recent_performance', {}):
            hit_rate = summary['recent_performance']['cache_hit_rate']
            if hit_rate < 0.7:
                recommendations.append("Cache hit rate is low - consider increasing cache size or TTL")

        # Check validation speed
        if 'files_per_second' in summary.get('recent_performance', {}):
            files_per_sec = summary['recent_performance']['files_per_second']
            if files_per_sec < 1.0:
                recommendations.append("Validation speed is slow - consider parallel processing or rule optimization")

        # Check memory usage
        system_stats = summary.get('system_stats', {})
        if 'memory_average' in system_stats:
            memory_usage = system_stats['memory_average']
            if memory_usage > 80:
                recommendations.append("High memory usage detected - consider reducing cache size or processing fewer files simultaneously")

        # Check CPU usage
        if 'cpu_average' in system_stats:
            cpu_usage = system_stats['cpu_average']
            if cpu_usage > 90:
                recommendations.append("High CPU usage detected - consider reducing parallel processing or optimizing rule patterns")

        return recommendations
