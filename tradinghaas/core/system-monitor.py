import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set
import psutil
import numpy as np
from collections import defaultdict

class AlertLevel(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class MetricType(Enum):
    SYSTEM = "SYSTEM"
    TRADING = "TRADING"
    EXECUTION = "EXECUTION"
    PERFORMANCE = "PERFORMANCE"

@dataclass
class SystemMetrics:
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_latency: float
    message_queue_size: int
    active_agents: int
    error_count: int
    timestamp: datetime

@dataclass
class Alert:
    level: AlertLevel
    source: str
    message: str
    timestamp: datetime
    metric_type: MetricType
    value: float
    threshold: float
    metadata: Dict

class SystemMonitor:
    """
    System Monitor for tracking system health, performance, and generating alerts.
    Includes performance metrics, health checks, and diagnostic capabilities.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("SystemMonitor")
        
        # Monitoring Thresholds
        self.thresholds = {
            'cpu_usage': 80.0,  # 80% CPU usage
            'memory_usage': 85.0,  # 85% memory usage
            'disk_usage': 90.0,  # 90% disk usage
            'network_latency': 100.0,  # 100ms latency
            'message_queue_size': 1000,  # 1000 messages
            'error_rate': 0.05,  # 5% error rate
            'execution_latency': 500.0  # 500ms execution latency
        }
        
        # Performance Tracking
        self.metrics_history = defaultdict(list)
        self.alerts_history = []
        self.active_alerts = set()
        
        # System State
        self.system_state = {}
        self.agent_states = {}
        self.component_health = {}
        
        # Monitoring Intervals
        self.monitoring_intervals = {
            MetricType.SYSTEM: 5,  # 5 seconds
            MetricType.TRADING: 1,  # 1 second
            MetricType.EXECUTION: 1,  # 1 second
            MetricType.PERFORMANCE: 60  # 60 seconds
        }
        
    async def initialize(self) -> bool:
        """Initialize the System Monitor."""
        try:
            # Initialize monitoring systems
            await self._initialize_monitoring()
            
            # Start monitoring tasks
            self.monitoring_tasks = {
                MetricType.SYSTEM: asyncio.create_task(self._monitor_system_metrics()),
                MetricType.TRADING: asyncio.create_task(self._monitor_trading_metrics()),
                MetricType.EXECUTION: asyncio.create_task(self._monitor_execution_metrics()),
                MetricType.PERFORMANCE: asyncio.create_task(self._monitor_performance_metrics())
            }
            
            self.logger.info("System Monitor initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Initialization failed: {str(e)}")
            return False

    async def _monitor_system_metrics(self):
        """Monitor system-level metrics."""
        while True:
            try:
                metrics = SystemMetrics(
                    cpu_usage=psutil.cpu_percent(),
                    memory_usage=psutil.virtual_memory().percent,
                    disk_usage=psutil.disk_usage('/').percent,
                    network_latency=await self._measure_network_latency(),
                    message_queue_size=await self._get_queue_size(),
                    active_agents=len(self.agent_states),
                    error_count=len(self.active_alerts),
                    timestamp=datetime.now()
                )
                
                await self._process_system_metrics(metrics)
                await asyncio.sleep(self.monitoring_intervals[MetricType.SYSTEM])
                
            except Exception as e:
                self.logger.error(f"System metrics monitoring failed: {str(e)}")
                await asyncio.sleep(1)

    async def _monitor_trading_metrics(self):
        """Monitor trading-related metrics."""
        while True:
            try:
                trading_metrics = await self._collect_trading_metrics()
                await self._process_trading_metrics(trading_metrics)
                await asyncio.sleep(self.monitoring_intervals[MetricType.TRADING])
                
            except Exception as e:
                self.logger.error(f"Trading metrics monitoring failed: {str(e)}")
                await asyncio.sleep(1)

    async def _monitor_execution_metrics(self):
        """Monitor execution-related metrics."""
        while True:
            try:
                execution_metrics = await self._collect_execution_metrics()
                await self._process_execution_metrics(execution_metrics)
                await asyncio.sleep(self.monitoring_intervals[MetricType.EXECUTION])
                
            except Exception as e:
                self.logger.error(f"Execution metrics monitoring failed: {str(e)}")
                await asyncio.sleep(1)

    async def _process_system_metrics(self, metrics: SystemMetrics):
        """Process and analyze system metrics."""
        try:
            # Check CPU usage
            if metrics.cpu_usage > self.thresholds['cpu_usage']:
                await self._generate_alert(
                    AlertLevel.WARNING,
                    "System",
                    f"High CPU usage: {metrics.cpu_usage}%",
                    MetricType.SYSTEM,
                    metrics.cpu_usage,
                    self.thresholds['cpu_usage']
                )
            
            # Check memory usage
            if metrics.memory_usage > self.thresholds['memory_usage']:
                await self._generate_alert(
                    AlertLevel.WARNING,
                    "System",
                    f"High memory usage: {metrics.memory_usage}%",
                    MetricType.SYSTEM,
                    metrics.memory_usage,
                    self.thresholds['memory_usage']
                )
            
            # Update metrics history
            self.metrics_history[MetricType.SYSTEM].append(metrics)
            
            # Trim history if needed
            if len(self.metrics_history[MetricType.SYSTEM]) > 1000:
                self.metrics_history[MetricType.SYSTEM] = self.metrics_history[MetricType.SYSTEM][-1000:]
                
        except Exception as e:
            self.logger.error(f"System metrics processing failed: {str(e)}")

    async def _generate_alert(self, level: AlertLevel, source: str, message: str,
                            metric_type: MetricType, value: float, threshold: float):
        """Generate and process system alerts."""
        try:
            alert = Alert(
                level=level,
                source=source,
                message=message,
                timestamp=datetime.now(),
                metric_type=metric_type,
                value=value,
                threshold=threshold,
                metadata={}
            )
            
            # Add to active alerts
            alert_key = f"{source}:{message}"
            self.active_alerts.add(alert_key)
            
            # Add to history
            self.alerts_history.append(alert)
            
            # Log alert
            self.logger.log(
                logging.CRITICAL if level == AlertLevel.CRITICAL else
                logging.ERROR if level == AlertLevel.ERROR else
                logging.WARNING if level == AlertLevel.WARNING else
                logging.INFO,
                f"Alert: {message}"
            )
            
            # Take immediate action for critical alerts
            if level == AlertLevel.CRITICAL:
                await self._handle_critical_alert(alert)
                
        except Exception as e:
            self.logger.error(f"Alert generation failed: {str(e)}")

    async def _handle_critical_alert(self, alert: Alert):
        """Handle critical system alerts."""
        try:
            # Log critical alert
            self.logger.critical(f"Critical alert: {alert.message}")
            
            # Take immediate action based on alert type
            if alert.metric_type == MetricType.SYSTEM:
                await self._handle_system_critical(alert)
            elif alert.metric_type == MetricType.TRADING:
                await self._handle_trading_critical(alert)
            elif alert.metric_type == MetricType.EXECUTION:
                await self._handle_execution_critical(alert)
                
        except Exception as e:
            self.logger.error(f"Critical alert handling failed: {str(e)}")

    async def get_system_health(self) -> Dict:
        """Get current system health status."""
        try:
            return {
                'system_metrics': self.metrics_history[MetricType.SYSTEM][-1].__dict__,
                'active_alerts': len(self.active_alerts),
                'component_health': self.component_health,
                'agent_states': self.agent_states,
                'is_healthy': len(self.active_alerts) == 0,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"Health status retrieval failed: {str(e)}")
            return {}

    async def get_performance_metrics(self) -> Dict:
        """Get system performance metrics."""
        try:
            return {
                'system_performance': {
                    'cpu_usage_avg': np.mean([m.cpu_usage for m in self.metrics_history[MetricType.SYSTEM][-100:]]),
                    'memory_usage_avg': np.mean([m.memory_usage for m in self.metrics_history[MetricType.SYSTEM][-100:]]),
                    'network_latency_avg': np.mean([m.network_latency for m in self.metrics_history[MetricType.SYSTEM][-100:]])
                },
                'trading_performance': await self._get_trading_performance(),
                'execution_performance': await self._get_execution_performance(),
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"Performance metrics retrieval failed: {str(e)}")
            return {}

    async def shutdown(self):
        """Clean shutdown of the System Monitor."""
        try:
            # Cancel all monitoring tasks
            for task in self.monitoring_tasks.values():
                task.cancel()
            
            # Save monitoring data
            await self._save_monitoring_data()
            
            # Clear alerts
            self.active_alerts.clear()
            
            self.logger.info("System Monitor shut down successfully")
            
        except Exception as e:
            self.logger.error(f"Shutdown failed: {str(e)}")
