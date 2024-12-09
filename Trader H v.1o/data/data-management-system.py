import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Union
import pandas as pd
import numpy as np
import aioredis
import motor.motor_asyncio
from pymongo import ASCENDING, DESCENDING
import clickhouse_driver
import aiofiles

class DataType(Enum):
    MARKET_DATA = "market_data"
    TRADING_SIGNALS = "trading_signals"
    SYSTEM_METRICS = "system_metrics"
    EXECUTION_DATA = "execution_data"
    ANALYTICS = "analytics"

class StorageType(Enum):
    REDIS = "redis"          # Fast access cache
    MONGODB = "mongodb"      # Document storage
    CLICKHOUSE = "clickhouse"  # Time-series data
    FILE = "file"           # Raw data storage

@dataclass
class DataConfig:
    retention_period: timedelta
    storage_type: StorageType
    compression_level: int
    batch_size: int
    index_fields: List[str]

class DataManagementSystem:
    """
    Data Management System for handling various types of trading system data.
    Includes data storage, retrieval, and optimization capabilities.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("DataManagementSystem")
        
        # Storage configurations
        self.storage_configs = {
            DataType.MARKET_DATA: DataConfig(
                retention_period=timedelta(days=30),
                storage_type=StorageType.CLICKHOUSE,
                compression_level=9,
                batch_size=1000,
                index_fields=['symbol', 'timestamp']
            ),
            DataType.TRADING_SIGNALS: DataConfig(
                retention_period=timedelta(days=7),
                storage_type=StorageType.MONGODB,
                compression_level=6,
                batch_size=100,
                index_fields=['symbol', 'timestamp', 'signal_type']
            ),
            DataType.SYSTEM_METRICS: DataConfig(
                retention_period=timedelta(days=14),
                storage_type=StorageType.CLICKHOUSE,
                compression_level=7,
                batch_size=500,
                index_fields=['component', 'timestamp', 'metric_type']
            ),
            DataType.EXECUTION_DATA: DataConfig(
                retention_period=timedelta(days=90),
                storage_type=StorageType.MONGODB,
                compression_level=8,
                batch_size=50,
                index_fields=['order_id', 'timestamp', 'status']
            )
        }
        
        # Database connections
        self.connections = {}
        
        # Data buffers
        self.write_buffers = {
            data_type: [] for data_type in DataType
        }
        
        # Cache configuration
        self.cache_config = {
            'max_size': 10000,
            'ttl': 3600  # 1 hour
        }
        
    async def initialize(self) -> bool:
        """Initialize the Data Management System."""
        try:
            # Initialize database connections
            self.connections[StorageType.REDIS] = await aioredis.create_redis_pool(
                'redis://localhost'
            )
            
            self.connections[StorageType.MONGODB] = motor.motor_asyncio.AsyncIOMotorClient(
                'mongodb://localhost:27017'
            )
            
            self.connections[StorageType.CLICKHOUSE] = clickhouse_driver.Client(
                host='localhost'
            )
            
            # Initialize databases and collections
            await self._initialize_storage()
            
            # Start background tasks
            self.tasks = {
                'buffer_flush': asyncio.create_task(self._flush_buffers()),
                'data_cleanup': asyncio.create_task(self._cleanup_old_data())
            }
            
            self.logger.info("Data Management System initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Initialization failed: {str(e)}")
            return False

    async def store_data(self, data_type: DataType, data: Union[Dict, List[Dict]]) -> bool:
        """Store data of specified type."""
        try:
            config = self.storage_configs[data_type]
            
            # Convert single item to list
            if isinstance(data, dict):
                data = [data]
            
            # Add to write buffer
            self.write_buffers[data_type].extend(data)
            
            # Flush if buffer size exceeds batch size
            if len(self.write_buffers[data_type]) >= config.batch_size:
                await self._flush_buffer(data_type)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Data storage failed: {str(e)}")
            return False

    async def query_data(self, data_type: DataType, query: Dict,
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None,
                        limit: Optional[int] = None) -> List[Dict]:
        """Query data with specified criteria."""
        try:
            # Check cache first
            cache_key = self._generate_cache_key(data_type, query, start_time, end_time)
            cached_data = await self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
            
            # Build query
            final_query = self._build_query(query, start_time, end_time)
            
            # Execute query based on storage type
            config = self.storage_configs[data_type]
            if config.storage_type == StorageType.MONGODB:
                data = await self._query_mongodb(data_type, final_query, limit)
            elif config.storage_type == StorageType.CLICKHOUSE:
                data = await self._query_clickhouse(data_type, final_query, limit)
            else:
                raise ValueError(f"Unsupported query storage type: {config.storage_type}")
            
            # Cache results
            await self._store_in_cache(cache_key, data)
            
            return data
            
        except Exception as e:
            self.logger.error(f"Data query failed: {str(e)}")
            return []

    async def _flush_buffer(self, data_type: DataType):
        """Flush write buffer for specified data type."""
        try:
            if not self.write_buffers[data_type]:
                return
            
            config = self.storage_configs[data_type]
            data = self.write_buffers[data_type]
            
            if config.storage_type == StorageType.MONGODB:
                await self._store_mongodb(data_type, data)
            elif config.storage_type == StorageType.CLICKHOUSE:
                await self._store_clickhouse(data_type, data)
            elif config.storage_type == StorageType.FILE:
                await self._store_file(data_type, data)
            
            # Clear buffer
            self.write_buffers[data_type] = []
            
        except Exception as e:
            self.logger.error(f"Buffer flush failed: {str(e)}")

    async def _store_mongodb(self, data_type: DataType, data: List[Dict]):
        """Store data in MongoDB."""
        try:
            db = self.connections[StorageType.MONGODB].trading_system
            collection = db[data_type.value]
            
            # Insert data
            await collection.insert_many(data)
            
        except Exception as e:
            self.logger.error(f"MongoDB storage failed: {str(e)}")
            raise

    async def _store_clickhouse(self, data_type: DataType, data: List[Dict]):
        """Store data in ClickHouse."""
        try:
            # Convert data to DataFrame for batch insert
            df = pd.DataFrame(data)
            
            # Execute insert
            self.connections[StorageType.CLICKHOUSE].execute(
                f'INSERT INTO {data_type.value} VALUES',
                df.to_dict('records')
            )
            
        except Exception as e:
            self.logger.error(f"ClickHouse storage failed: {str(e)}")
            raise

    async def _get_from_cache(self, cache_key: str) -> Optional[List[Dict]]:
        """Retrieve data from Redis cache."""
        try:
            cached = await self.connections[StorageType.REDIS].get(cache_key)
            if cached:
                return json.loads(cached)
            return None
            
        except Exception as e:
            self.logger.error(f"Cache retrieval failed: {str(e)}")
            return None

    async def _store_in_cache(self, cache_key: str, data: List[Dict]):
        """Store data in Redis cache."""
        try:
            await self.connections[StorageType.REDIS].setex(
                cache_key,
                self.cache_config['ttl'],
                json.dumps(data)
            )
            
        except Exception as e:
            self.logger.error(f"Cache storage failed: {str(e)}")

    async def _cleanup_old_data(self):
        """Clean up expired data periodically."""
        while True:
            try:
                for data_type, config in self.storage_configs.items():
                    cutoff_time = datetime.now() - config.retention_period
                    
                    if config.storage_type == StorageType.MONGODB:
                        db = self.connections[StorageType.MONGODB].trading_system
                        await db[data_type.value].delete_many({
                            'timestamp': {'$lt': cutoff_time}
                        })
                    elif config.storage_type == StorageType.CLICKHOUSE:
                        self.connections[StorageType.CLICKHOUSE].execute(
                            f'ALTER TABLE {data_type.value} DELETE WHERE timestamp < %s',
                            (cutoff_time,)
                        )
                
                await asyncio.sleep(3600)  # Run every hour
                
            except Exception as e:
                self.logger.error(f"Data cleanup failed: {str(e)}")
                await asyncio.sleep(300)  # Back off on error

    async def optimize_storage(self, data_type: DataType):
        """Optimize storage for specific data type."""
        try:
            config = self.storage_configs[data_type]
            
            if config.storage_type == StorageType.MONGODB:
                # Rebuild indexes
                db = self.connections[StorageType.MONGODB].trading_system
                await db[data_type.value].reindex()
                
            elif config.storage_type == StorageType.CLICKHOUSE:
                # Optimize table
                self.connections[StorageType.CLICKHOUSE].execute(
                    f'OPTIMIZE TABLE {data_type.value} FINAL'
                )
            
        except Exception as e:
            self.logger.error(f"Storage optimization failed: {str(e)}")

    async def get_storage_stats(self) -> Dict:
        """Get storage statistics."""
        try:
            stats = {}
            
            for data_type in DataType:
                config = self.storage_configs[data_type]
                
                if config.storage_type == StorageType.MONGODB:
                    db = self.connections[StorageType.MONGODB].trading_system
                    stats[data_type.value] = {
                        'count': await db[data_type.value].count_documents({}),
                        'size': await db.command('collstats', data_type.value)['size'],
                        'indexes': len(config.index_fields)
                    }
                elif config.storage_type == StorageType.CLICKHOUSE:
                    stats[data_type.value] = {
                        'rows': self.connections[StorageType.CLICKHOUSE].execute(
                            f'SELECT count() FROM {data_type.value}'
                        )[0][0],
                        'size': self.connections[StorageType.CLICKHOUSE].execute(
                            f'SELECT total_bytes FROM system.tables WHERE name = %s',
                            (data_type.value,)
                        )[0][0]
                    }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Stats retrieval failed: {str(e)}")
            return {}

    async def shutdown(self):
        """Clean shutdown of the Data Management System."""
        try:
            # Flush all buffers
            for data_type in DataType:
                await self._flush_buffer(data_type)
            
            # Cancel background tasks
            for task in self.tasks.values():
                task.cancel()
            
            # Close connections
            for connection in self.connections.values():
                await connection.close()
            
            self.logger.info("Data Management System shut down successfully")
            
        except Exception as e:
            self.logger.error(f"Shutdown failed: {str(e)}")
