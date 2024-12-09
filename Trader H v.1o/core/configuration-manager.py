import yaml
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
import asyncio
from pathlib import Path
import jsonschema
from enum import Enum

class ConfigType(Enum):
    SYSTEM = "system"
    AGENT = "agent"
    RISK = "risk"
    EXECUTION = "execution"
    MONITORING = "monitoring"

@dataclass
class SystemConfig:
    env: str  # 'development', 'staging', 'production'
    debug_mode: bool
    log_level: str
    max_memory_usage: float
    max_cpu_usage: float
    data_retention_days: int

@dataclass
class AgentConfig:
    name: str
    enabled: bool
    update_interval: float
    batch_size: int
    max_positions: int
    parameters: Dict

@dataclass
class RiskConfig:
    max_position_size: float
    max_portfolio_risk: float
    max_leverage: float
    max_correlation: float
    max_sector_exposure: float
    emergency_cash_buffer: float

@dataclass
class ExecutionConfig:
    max_slippage: float
    min_fill_rate: float
    execution_timeout: float
    retry_attempts: int
    order_types: List[str]

@dataclass
class MonitoringConfig:
    alert_levels: Dict[str, float]
    metrics_interval: float
    health_check_interval: float
    log_retention_days: int

class ConfigurationManager:
    """
    Configuration Manager for handling system-wide settings and parameters.
    Includes validation, persistence, and real-time updates.
    """
    
    def __init__(self, config_dir: str):
        self.logger = logging.getLogger("ConfigurationManager")
        self.config_dir = Path(config_dir)
        
        # Configuration Storage
        self.configurations = {}
        self.schema_validators = {}
        self.active_subscriptions = {}
        
        # Change Tracking
        self.config_history = {}
        self.pending_changes = {}
        
        # Validation Rules
        self.validation_rules = self._load_validation_rules()
        
    async def initialize(self) -> bool:
        """Initialize the Configuration Manager."""
        try:
            # Create config directory if it doesn't exist
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            # Load schemas
            await self._load_schemas()
            
            # Load configurations
            await self._load_configurations()
            
            # Initialize change monitoring
            self.change_monitor = asyncio.create_task(
                self._monitor_configuration_changes()
            )
            
            self.logger.info("Configuration Manager initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Initialization failed: {str(e)}")
            return False

    async def get_config(self, config_type: ConfigType, 
                        component: str = None) -> Dict:
        """Retrieve configuration settings."""
        try:
            config_key = f"{config_type.value}.{component}" if component else config_type.value
            
            if config_key not in self.configurations:
                raise KeyError(f"Configuration not found: {config_key}")
            
            return self.configurations[config_key]
            
        except Exception as e:
            self.logger.error(f"Configuration retrieval failed: {str(e)}")
            return {}

    async def update_config(self, config_type: ConfigType, 
                          updates: Dict, component: str = None) -> bool:
        """Update configuration settings."""
        try:
            config_key = f"{config_type.value}.{component}" if component else config_type.value
            
            # Validate updates
            if not await self._validate_config(config_type, updates):
                raise ValueError("Invalid configuration updates")
            
            # Store current config for rollback
            current_config = self.configurations.get(config_key, {})
            
            # Apply updates
            new_config = {**current_config, **updates}
            
            # Validate complete configuration
            if not await self._validate_config(config_type, new_config):
                raise ValueError("Invalid resulting configuration")
            
            # Store update
            self.configurations[config_key] = new_config
            
            # Record change
            await self._record_config_change(config_key, current_config, new_config)
            
            # Notify subscribers
            await self._notify_config_change(config_key, new_config)
            
            # Persist changes
            await self._save_configuration(config_key)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Configuration update failed: {str(e)}")
            return False

    async def subscribe_to_changes(self, config_type: ConfigType,
                                 callback: callable, component: str = None) -> str:
        """Subscribe to configuration changes."""
        try:
            subscription_id = f"{datetime.now().timestamp()}"
            config_key = f"{config_type.value}.{component}" if component else config_type.value
            
            if config_key not in self.active_subscriptions:
                self.active_subscriptions[config_key] = {}
            
            self.active_subscriptions[config_key][subscription_id] = callback
            
            return subscription_id
            
        except Exception as e:
            self.logger.error(f"Subscription failed: {str(e)}")
            return None

    async def _load_schemas(self):
        """Load JSON schemas for configuration validation."""
        try:
            schema_dir = self.config_dir / "schemas"
            for schema_file in schema_dir.glob("*.json"):
                with open(schema_file) as f:
                    schema = json.load(f)
                    self.schema_validators[schema_file.stem] = jsonschema.Draft7Validator(schema)
                    
        except Exception as e:
            self.logger.error(f"Schema loading failed: {str(e)}")
            raise

    async def _load_configurations(self):
        """Load configurations from files."""
        try:
            for config_file in self.config_dir.glob("*.yaml"):
                with open(config_file) as f:
                    config = yaml.safe_load(f)
                    config_type = config_file.stem
                    
                    if await self._validate_config(ConfigType(config_type), config):
                        self.configurations[config_type] = config
                    else:
                        raise ValueError(f"Invalid configuration in {config_file}")
                        
        except Exception as e:
            self.logger.error(f"Configuration loading failed: {str(e)}")
            raise

    async def _validate_config(self, config_type: ConfigType, config: Dict) -> bool:
        """Validate configuration against schema."""
        try:
            validator = self.schema_validators.get(config_type.value)
            if not validator:
                raise ValueError(f"No validator found for {config_type.value}")
            
            validator.validate(config)
            return True
            
        except jsonschema.exceptions.ValidationError as e:
            self.logger.error(f"Configuration validation failed: {str(e)}")
            return False

    async def _save_configuration(self, config_key: str):
        """Persist configuration changes to file."""
        try:
            config_file = self.config_dir / f"{config_key}.yaml"
            config_data = self.configurations[config_key]
            
            # Create backup
            if config_file.exists():
                backup_file = config_file.with_suffix(f".bak.{datetime.now().timestamp()}")
                config_file.rename(backup_file)
            
            # Save new configuration
            with open(config_file, 'w') as f:
                yaml.safe_dump(config_data, f)
                
        except Exception as e:
            self.logger.error(f"Configuration save failed: {str(e)}")
            raise

    async def _notify_config_change(self, config_key: str, new_config: Dict):
        """Notify subscribers of configuration changes."""
        try:
            subscribers = self.active_subscriptions.get(config_key, {})
            
            for callback in subscribers.values():
                try:
                    await callback(new_config)
                except Exception as e:
                    self.logger.error(f"Subscriber notification failed: {str(e)}")
                    
        except Exception as e:
            self.logger.error(f"Change notification failed: {str(e)}")

    async def _monitor_configuration_changes(self):
        """Monitor for configuration file changes."""
        while True:
            try:
                # Check for file changes
                for config_file in self.config_dir.glob("*.yaml"):
                    last_modified = config_file.stat().st_mtime
                    stored_time = self.config_history.get(config_file.stem, 0)
                    
                    if last_modified > stored_time:
                        # Reload configuration
                        with open(config_file) as f:
                            new_config = yaml.safe_load(f)
                            
                        if await self._validate_config(
                            ConfigType(config_file.stem), new_config
                        ):
                            self.configurations[config_file.stem] = new_config
                            self.config_history[config_file.stem] = last_modified
                            
                            # Notify subscribers
                            await self._notify_config_change(
                                config_file.stem, new_config
                            )
                
                await asyncio.sleep(1)  # Check every second
                
            except Exception as e:
                self.logger.error(f"Configuration monitoring failed: {str(e)}")
                await asyncio.sleep(5)  # Back off on error

    def _load_validation_rules(self) -> Dict:
        """Load validation rules for configurations."""
        return {
            ConfigType.SYSTEM: {
                'required_fields': ['env', 'debug_mode', 'log_level'],
                'value_ranges': {
                    'max_memory_usage': (0.0, 1.0),
                    'max_cpu_usage': (0.0, 1.0)
                }
            },
            ConfigType.RISK: {
                'required_fields': ['max_position_size', 'max_portfolio_risk'],
                'value_ranges': {
                    'max_position_size': (0.0, 1.0),
                    'max_portfolio_risk': (0.0, 1.0),
                    'max_leverage': (1.0, 10.0)
                }
            }
        }

    async def shutdown(self):
        """Clean shutdown of the Configuration Manager."""
        try:
            # Cancel monitoring task
            if self.change_monitor:
                self.change_monitor.cancel()
            
            # Save any pending changes
            for config_key in self.pending_changes:
                await self._save_configuration(config_key)
            
            self.logger.info("Configuration Manager shut down successfully")
            
        except Exception as e:
            self.logger.error(f"Shutdown failed: {str(e)}")
