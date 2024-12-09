import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
import docker
import kubernetes
from kubernetes import client, config
import yaml
import os
from pathlib import Path

class DeploymentState(Enum):
    PENDING = "PENDING"
    DEPLOYING = "DEPLOYING"
    RUNNING = "RUNNING"
    UPDATING = "UPDATING"
    FAILED = "FAILED"
    STOPPED = "STOPPED"

class ResourceType(Enum):
    AGENT = "AGENT"
    SERVICE = "SERVICE"
    DATABASE = "DATABASE"
    QUEUE = "QUEUE"
    CACHE = "CACHE"

@dataclass
class ResourceConfig:
    name: str
    type: ResourceType
    replicas: int
    cpu_limit: str
    memory_limit: str
    storage_limit: Optional[str]
    environment: Dict[str, str]
    dependencies: List[str]

class DeploymentManager:
    """
    Deployment Manager for orchestrating system components and managing resources.
    Handles deployment, scaling, and resource management.
    """
    
    def __init__(self, config_path: str):
        self.logger = logging.getLogger("DeploymentManager")
        self.config_path = Path(config_path)
        
        # Kubernetes configuration
        self.k8s_config = None
        self.k8s_client = None
        
        # Resource tracking
        self.resources = {}
        self.deployment_states = {}
        self.health_checks = {}
        
        # Scaling parameters
        self.scaling_thresholds = {
            'cpu_threshold': 0.8,
            'memory_threshold': 0.8,
            'queue_threshold': 1000
        }
        
    async def initialize(self) -> bool:
        """Initialize the Deployment Manager."""
        try:
            # Load Kubernetes configuration
            config.load_kube_config()
            self.k8s_client = client.ApiClient()
            self.k8s_api = client.AppsV1Api(self.k8s_client)
            
            # Load deployment configurations
            await self._load_configurations()
            
            # Initialize resource monitoring
            self.monitor_task = asyncio.create_task(
                self._monitor_resources()
            )
            
            self.logger.info("Deployment Manager initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Initialization failed: {str(e)}")
            return False

    async def deploy_system(self) -> bool:
        """Deploy the complete trading system."""
        try:
            # Create namespace if it doesn't exist
            await self._ensure_namespace()
            
            # Deploy core infrastructure
            if not await self._deploy_infrastructure():
                raise Exception("Infrastructure deployment failed")
            
            # Deploy agents in dependency order
            deployment_order = self._calculate_deployment_order()
            for resource_name in deployment_order:
                if not await self.deploy_resource(resource_name):
                    raise Exception(f"Resource deployment failed: {resource_name}")
            
            self.logger.info("System deployment completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"System deployment failed: {str(e)}")
            return False

    async def deploy_resource(self, resource_name: str) -> bool:
        """Deploy a single resource."""
        try:
            resource_config = self.resources[resource_name]
            self.deployment_states[resource_name] = DeploymentState.DEPLOYING
            
            # Create deployment
            deployment = self._create_deployment_config(resource_config)
            await self._apply_deployment(deployment)
            
            # Create service if needed
            if resource_config.type in [ResourceType.SERVICE, ResourceType.DATABASE]:
                service = self._create_service_config(resource_config)
                await self._apply_service(service)
            
            # Wait for deployment to be ready
            if await self._wait_for_deployment(resource_name):
                self.deployment_states[resource_name] = DeploymentState.RUNNING
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Resource deployment failed: {str(e)}")
            self.deployment_states[resource_name] = DeploymentState.FAILED
            return False

    async def update_resource(self, resource_name: str, 
                            updates: Dict) -> bool:
        """Update an existing resource."""
        try:
            if resource_name not in self.resources:
                raise ValueError(f"Resource not found: {resource_name}")
            
            resource_config = self.resources[resource_name]
            self.deployment_states[resource_name] = DeploymentState.UPDATING
            
            # Update configuration
            updated_config = {**resource_config.__dict__, **updates}
            new_config = ResourceConfig(**updated_config)
            
            # Apply updates
            deployment = self._create_deployment_config(new_config)
            await self._apply_deployment(deployment)
            
            # Wait for update to complete
            if await self._wait_for_deployment(resource_name):
                self.resources[resource_name] = new_config
                self.deployment_states[resource_name] = DeploymentState.RUNNING
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Resource update failed: {str(e)}")
            return False

    async def scale_resource(self, resource_name: str, replicas: int) -> bool:
        """Scale a resource to specified number of replicas."""
        try:
            if resource_name not in self.resources:
                raise ValueError(f"Resource not found: {resource_name}")
            
            # Update deployment
            deployment = self.k8s_api.read_namespaced_deployment(
                name=resource_name,
                namespace="trading-system"
            )
            
            deployment.spec.replicas = replicas
            
            self.k8s_api.patch_namespaced_deployment(
                name=resource_name,
                namespace="trading-system",
                body=deployment
            )
            
            # Wait for scaling to complete
            if await self._wait_for_deployment(resource_name):
                self.resources[resource_name].replicas = replicas
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Resource scaling failed: {str(e)}")
            return False

    async def _monitor_resources(self):
        """Monitor resource utilization and health."""
        while True:
            try:
                for resource_name, resource in self.resources.items():
                    # Skip if not running
                    if self.deployment_states[resource_name] != DeploymentState.RUNNING:
                        continue
                    
                    # Get metrics
                    metrics = await self._get_resource_metrics(resource_name)
                    
                    # Check thresholds
                    if await self._check_scaling_needed(resource_name, metrics):
                        # Calculate new replica count
                        new_replicas = await self._calculate_replicas(
                            resource_name, metrics
                        )
                        
                        # Scale resource
                        await self.scale_resource(resource_name, new_replicas)
                    
                    # Update health status
                    self.health_checks[resource_name] = await self._check_health(
                        resource_name
                    )
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Resource monitoring failed: {str(e)}")
                await asyncio.sleep(60)  # Back off on error

    def _create_deployment_config(self, resource_config: ResourceConfig) -> Dict:
        """Create Kubernetes deployment configuration."""
        return {
            'apiVersion': 'apps/v1',
            'kind': 'Deployment',
            'metadata': {
                'name': resource_config.name,
                'namespace': 'trading-system'
            },
            'spec': {
                'replicas': resource_config.replicas,
                'selector': {
                    'matchLabels': {
                        'app': resource_config.name
                    }
                },
                'template': {
                    'metadata': {
                        'labels': {
                            'app': resource_config.name
                        }
                    },
                    'spec': {
                        'containers': [{
                            'name': resource_config.name,
                            'image': f'trading-system/{resource_config.name}:latest',
                            'resources': {
                                'limits': {
                                    'cpu': resource_config.cpu_limit,
                                    'memory': resource_config.memory_limit
                                }
                            },
                            'env': [
                                {'name': k, 'value': v}
                                for k, v in resource_config.environment.items()
                            ]
                        }]
                    }
                }
            }
        }

    async def _calculate_deployment_order(self) -> List[str]:
        """Calculate deployment order based on dependencies."""
        deployed = set()
        deployment_order = []
        
        def can_deploy(resource_name):
            return all(dep in deployed for dep in 
                      self.resources[resource_name].dependencies)
        
        while len(deployed) < len(self.resources):
            deployable = [
                name for name in self.resources
                if name not in deployed and can_deploy(name)
            ]
            
            if not deployable:
                raise Exception("Circular dependency detected")
            
            for resource_name in deployable:
                deployment_order.append(resource_name)
                deployed.add(resource_name)
        
        return deployment_order

    async def _wait_for_deployment(self, resource_name: str, 
                                 timeout: int = 300) -> bool:
        """Wait for deployment to be ready."""
        try:
            start_time = datetime.now()
            while (datetime.now() - start_time).seconds < timeout:
                deployment = self.k8s_api.read_namespaced_deployment_status(
                    name=resource_name,
                    namespace="trading-system"
                )
                
                if (deployment.status.available_replicas == 
                    deployment.spec.replicas):
                    return True
                
                await asyncio.sleep(5)
            
            return False
            
        except Exception as e:
            self.logger.error(f"Deployment status check failed: {str(e)}")
            return False

    async def shutdown(self):
        """Clean shutdown of the Deployment Manager."""
        try:
            # Cancel monitoring task
            if self.monitor_task:
                self.monitor_task.cancel()
            
            # Stop all resources
            for resource_name in self.resources:
                await self._stop_resource(resource_name)
            
            self.logger.info("Deployment Manager shut down successfully")
            
        except Exception as e:
            self.logger.error(f"Shutdown failed: {str(e)}")
