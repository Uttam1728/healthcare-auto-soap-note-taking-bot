"""
Performance monitoring and metrics collection for the healthcare SOAP note taking bot.
Provides comprehensive monitoring of system performance and resource usage.
"""

import time
import threading
import psutil
import os
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from collections import deque, defaultdict
from datetime import datetime, timedelta
import json
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class MetricPoint:
    """Represents a single metric measurement"""
    timestamp: float
    value: float
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp,
            'value': self.value,
            'tags': self.tags
        }


class TimeSeries:
    """Time series data structure for metrics"""
    
    def __init__(self, max_points: int = 1000):
        self.max_points = max_points
        self.points: deque = deque(maxlen=max_points)
        self.lock = threading.Lock()
    
    def add_point(self, value: float, tags: Dict[str, str] = None):
        """Add a new data point"""
        with self.lock:
            point = MetricPoint(
                timestamp=time.time(),
                value=value,
                tags=tags or {}
            )
            self.points.append(point)
    
    def get_points(self, since: Optional[float] = None) -> List[MetricPoint]:
        """Get points since timestamp"""
        with self.lock:
            if since is None:
                return list(self.points)
            return [p for p in self.points if p.timestamp >= since]
    
    def get_latest(self) -> Optional[MetricPoint]:
        """Get the latest point"""
        with self.lock:
            return self.points[-1] if self.points else None
    
    def get_average(self, since: Optional[float] = None) -> float:
        """Get average value since timestamp"""
        points = self.get_points(since)
        if not points:
            return 0.0
        return sum(p.value for p in points) / len(points)
    
    def get_max(self, since: Optional[float] = None) -> float:
        """Get maximum value since timestamp"""
        points = self.get_points(since)
        if not points:
            return 0.0
        return max(p.value for p in points)
    
    def get_min(self, since: Optional[float] = None) -> float:
        """Get minimum value since timestamp"""
        points = self.get_points(since)
        if not points:
            return 0.0
        return min(p.value for p in points)


class PerformanceCounter:
    """Performance counter for tracking operations"""
    
    def __init__(self):
        self.count = 0
        self.total_time = 0.0
        self.min_time = float('inf')
        self.max_time = 0.0
        self.lock = threading.Lock()
    
    def record(self, duration: float):
        """Record an operation duration"""
        with self.lock:
            self.count += 1
            self.total_time += duration
            self.min_time = min(self.min_time, duration)
            self.max_time = max(self.max_time, duration)
    
    def get_stats(self) -> Dict[str, float]:
        """Get performance statistics"""
        with self.lock:
            if self.count == 0:
                return {
                    'count': 0,
                    'average_time': 0.0,
                    'min_time': 0.0,
                    'max_time': 0.0,
                    'total_time': 0.0
                }
            
            return {
                'count': self.count,
                'average_time': self.total_time / self.count,
                'min_time': self.min_time if self.min_time != float('inf') else 0.0,
                'max_time': self.max_time,
                'total_time': self.total_time
            }
    
    def reset(self):
        """Reset the counter"""
        with self.lock:
            self.count = 0
            self.total_time = 0.0
            self.min_time = float('inf')
            self.max_time = 0.0


class MetricsCollector:
    """Centralized metrics collection system"""
    
    def __init__(self):
        self.time_series: Dict[str, TimeSeries] = {}
        self.counters: Dict[str, PerformanceCounter] = {}
        self.gauges: Dict[str, float] = {}
        self.lock = threading.Lock()
        self.start_time = time.time()
        
        # System metrics collection
        self.system_metrics_enabled = True
        self.collection_thread = None
        self.collection_interval = 30  # seconds
        
        # Start system metrics collection
        self.start_system_metrics_collection()
    
    def record_metric(self, name: str, value: float, tags: Dict[str, str] = None):
        """Record a metric value"""
        with self.lock:
            if name not in self.time_series:
                self.time_series[name] = TimeSeries()
            self.time_series[name].add_point(value, tags)
    
    def record_counter(self, name: str, duration: float):
        """Record a performance counter"""
        with self.lock:
            if name not in self.counters:
                self.counters[name] = PerformanceCounter()
            self.counters[name].record(duration)
    
    def set_gauge(self, name: str, value: float):
        """Set a gauge value"""
        with self.lock:
            self.gauges[name] = value
    
    def increment_gauge(self, name: str, amount: float = 1.0):
        """Increment a gauge value"""
        with self.lock:
            self.gauges[name] = self.gauges.get(name, 0.0) + amount
    
    def get_metric_stats(self, name: str, since: Optional[float] = None) -> Dict[str, float]:
        """Get statistics for a metric"""
        with self.lock:
            if name not in self.time_series:
                return {}
            
            ts = self.time_series[name]
            return {
                'average': ts.get_average(since),
                'max': ts.get_max(since),
                'min': ts.get_min(since),
                'latest': ts.get_latest().value if ts.get_latest() else 0.0,
                'count': len(ts.get_points(since))
            }
    
    def get_counter_stats(self, name: str) -> Dict[str, float]:
        """Get performance counter statistics"""
        with self.lock:
            if name not in self.counters:
                return {}
            return self.counters[name].get_stats()
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics and statistics"""
        with self.lock:
            result = {
                'timestamp': time.time(),
                'uptime': time.time() - self.start_time,
                'time_series': {},
                'counters': {},
                'gauges': dict(self.gauges)
            }
            
            # Get time series stats
            for name, ts in self.time_series.items():
                result['time_series'][name] = self.get_metric_stats(name)
            
            # Get counter stats
            for name, counter in self.counters.items():
                result['counters'][name] = counter.get_stats()
            
            return result
    
    def collect_system_metrics(self):
        """Collect system performance metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            self.record_metric('system.cpu.percent', cpu_percent)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            self.record_metric('system.memory.percent', memory.percent)
            self.record_metric('system.memory.used_bytes', memory.used)
            self.record_metric('system.memory.available_bytes', memory.available)
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            self.record_metric('system.disk.percent', disk.percent)
            self.record_metric('system.disk.used_bytes', disk.used)
            self.record_metric('system.disk.free_bytes', disk.free)
            
            # Process metrics
            process = psutil.Process(os.getpid())
            self.record_metric('process.cpu.percent', process.cpu_percent())
            self.record_metric('process.memory.rss_bytes', process.memory_info().rss)
            self.record_metric('process.memory.vms_bytes', process.memory_info().vms)
            self.record_metric('process.threads.count', process.num_threads())
            
            # File descriptors (Unix only)
            try:
                self.record_metric('process.file_descriptors.count', process.num_fds())
            except AttributeError:
                pass  # Not available on Windows
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    def start_system_metrics_collection(self):
        """Start background system metrics collection"""
        def collection_loop():
            while self.system_metrics_enabled:
                try:
                    self.collect_system_metrics()
                    time.sleep(self.collection_interval)
                except Exception as e:
                    logger.error(f"Error in metrics collection loop: {e}")
                    time.sleep(5)  # Short sleep on error
        
        self.collection_thread = threading.Thread(target=collection_loop, daemon=True)
        self.collection_thread.start()
        logger.info("Started system metrics collection")
    
    def stop_system_metrics_collection(self):
        """Stop background system metrics collection"""
        self.system_metrics_enabled = False
        if self.collection_thread:
            self.collection_thread.join(timeout=5)
        logger.info("Stopped system metrics collection")
    
    def export_metrics(self, format: str = 'json') -> str:
        """Export metrics in specified format"""
        metrics = self.get_all_metrics()
        
        if format == 'json':
            return json.dumps(metrics, indent=2)
        elif format == 'prometheus':
            return self._export_prometheus_format(metrics)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _export_prometheus_format(self, metrics: Dict[str, Any]) -> str:
        """Export metrics in Prometheus format"""
        lines = []
        
        # Gauges
        for name, value in metrics['gauges'].items():
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name} {value}")
        
        # Time series (latest values as gauges)
        for name, stats in metrics['time_series'].items():
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name} {stats.get('latest', 0)}")
        
        # Counters
        for name, stats in metrics['counters'].items():
            lines.append(f"# TYPE {name}_total counter")
            lines.append(f"{name}_total {stats.get('count', 0)}")
            lines.append(f"# TYPE {name}_duration_seconds gauge")
            lines.append(f"{name}_duration_seconds {stats.get('average_time', 0)}")
        
        return '\n'.join(lines)


# Global metrics collector instance
metrics_collector = MetricsCollector()


def record_metric(name: str, value: float, tags: Dict[str, str] = None):
    """Convenience function to record a metric"""
    metrics_collector.record_metric(name, value, tags)


def record_performance(name: str, duration: float):
    """Convenience function to record performance"""
    metrics_collector.record_counter(name, duration)


def set_gauge(name: str, value: float):
    """Convenience function to set a gauge"""
    metrics_collector.set_gauge(name, value)


def increment_counter(name: str, amount: float = 1.0):
    """Convenience function to increment a counter"""
    metrics_collector.increment_gauge(name, amount)


class performance_timer:
    """Context manager for timing operations"""
    
    def __init__(self, metric_name: str, tags: Dict[str, str] = None):
        self.metric_name = metric_name
        self.tags = tags or {}
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            record_performance(self.metric_name, duration)
            record_metric(f"{self.metric_name}.duration", duration, self.tags)


def monitor_performance(metric_name: str):
    """Decorator to monitor function performance"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with performance_timer(metric_name):
                return func(*args, **kwargs)
        return wrapper
    return decorator


# Application-specific metrics helpers
class HealthcareMetrics:
    """Healthcare-specific metrics tracking"""
    
    @staticmethod
    def record_transcription_event(event_type: str, session_id: str = None):
        """Record transcription events"""
        tags = {'event_type': event_type}
        if session_id:
            tags['session_id'] = session_id
        
        increment_counter('transcription.events.total')
        record_metric('transcription.events', 1, tags)
    
    @staticmethod
    def record_analysis_event(analysis_type: str, success: bool, duration: float):
        """Record analysis events"""
        tags = {
            'analysis_type': analysis_type,
            'success': str(success)
        }
        
        increment_counter('analysis.events.total')
        record_metric('analysis.events', 1, tags)
        record_performance('analysis.duration', duration)
    
    @staticmethod
    def record_session_event(event_type: str, session_id: str):
        """Record session events"""
        tags = {
            'event_type': event_type,
            'session_id': session_id
        }
        
        increment_counter('session.events.total')
        record_metric('session.events', 1, tags)
    
    @staticmethod
    def record_error(error_type: str, component: str):
        """Record error events"""
        tags = {
            'error_type': error_type,
            'component': component
        }
        
        increment_counter('errors.total')
        record_metric('errors', 1, tags)


# Initialize healthcare metrics
healthcare_metrics = HealthcareMetrics() 