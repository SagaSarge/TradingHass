import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from collections import defaultdict
import json
import uuid

class MessageType(Enum):
    MARKET_DATA = "MARKET_DATA"
    SIGNAL = "SIGNAL"
    ORDER = "ORDER"
    RISK = "RISK"
    EXECUTION = "EXECUTION"
    SYSTEM = "SYSTEM"
    CONTROL = "CONTROL"

class MessagePriority(Enum):
    HIGH = 0
    MEDIUM = 1
    LOW = 2

@dataclass
class Message:
    id: str
    type: MessageType
    priority: MessagePriority
    source: str
    destination: str
    timestamp: datetime
    payload: Dict
    correlation_id: Optional[str] = None
    metadata: Optional[Dict] = None

class IntegrationLayer:
    """
    Integration Layer for coordinating system-wide communication and data flow.
    Handles message routing, event processing, and agent coordination.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("IntegrationLayer")
        
        # Message Queues
        self.message_queues = {
            priority: asyncio.PriorityQueue() 
            for priority in MessagePriority
        }
        
        # Subscriptions
        self.subscriptions = defaultdict(set)
        
        # Event Handlers
        self.event_handlers = defaultdict(list)
        
        # Active Sessions
        self.active_sessions = {}
        
        # Message Statistics
        self.message_stats = defaultdict(int)
        
        # Flow Control
        self.rate_limits = {
            MessageType.MARKET_DATA: 1000,  # messages per second
            MessageType.SIGNAL: 100,
            MessageType.ORDER: 50,
            MessageType.RISK: 100,
            MessageType.EXECUTION: 50,
            MessageType.SYSTEM: 100,
            MessageType.CONTROL: 10
        }
        
    async def initialize(self) -> bool:
        """Initialize the Integration Layer."""
        try:
            # Start message processors
            self.processors = {
                priority: asyncio.create_task(self._process_message_queue(priority))
                for priority in MessagePriority
            }
            
            # Initialize rate limiters
            self.rate_limiters = {
                msg_type: asyncio.Semaphore(limit)
                for msg_type, limit in self.rate_limits.items()
            }
            
            self.logger.info("Integration Layer initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Initialization failed: {str(e)}")
            return False

    async def publish_message(self, message: Message) -> bool:
        """Publish a message to the system."""
        try:
            # Generate message ID if not provided
            if not message.id:
                message.id = str(uuid.uuid4())
            
            # Set timestamp if not provided
            if not message.timestamp:
                message.timestamp = datetime.now()
            
            # Apply rate limiting
            async with self.rate_limiters[message.type]:
                # Add to appropriate queue
                await self.message_queues[message.priority].put(
                    (message.priority.value, message)
                )
                
                # Update statistics
                self.message_stats[message.type] += 1
                
                return True
                
        except Exception as e:
            self.logger.error(f"Message publication failed: {str(e)}")
            return False

    async def subscribe(self, message_type: MessageType, callback: Callable,
                       filter_criteria: Optional[Dict] = None) -> str:
        """Subscribe to specific message types with optional filtering."""
        try:
            subscription_id = str(uuid.uuid4())
            
            self.subscriptions[message_type].add({
                'id': subscription_id,
                'callback': callback,
                'filter': filter_criteria
            })
            
            self.logger.info(f"New subscription added for {message_type.value}")
            return subscription_id
            
        except Exception as e:
            self.logger.error(f"Subscription failed: {str(e)}")
            return None

    async def _process_message_queue(self, priority: MessagePriority):
        """Process messages from a specific priority queue."""
        while True:
            try:
                # Get message from queue
                _, message = await self.message_queues[priority].get()
                
                # Process message
                await self._route_message(message)
                
                # Mark task as done
                self.message_queues[priority].task_done()
                
            except Exception as e:
                self.logger.error(f"Message processing failed: {str(e)}")
                await asyncio.sleep(0.1)

    async def _route_message(self, message: Message):
        """Route message to appropriate subscribers."""
        try:
            # Get subscribers for message type
            subscribers = self.subscriptions[message.type]
            
            # Route to each subscriber
            for subscriber in subscribers:
                if self._matches_filter(message, subscriber['filter']):
                    try:
                        await subscriber['callback'](message)
                    except Exception as e:
                        self.logger.error(f"Subscriber callback failed: {str(e)}")
                        
        except Exception as e:
            self.logger.error(f"Message routing failed: {str(e)}")

    def _matches_filter(self, message: Message, filter_criteria: Optional[Dict]) -> bool:
        """Check if message matches filter criteria."""
        if not filter_criteria:
            return True
            
        try:
            for key, value in filter_criteria.items():
                if key in message.metadata:
                    if message.metadata[key] != value:
                        return False
                elif key in message.payload:
                    if message.payload[key] != value:
                        return False
                else:
                    return False
            return True
            
        except Exception as e:
            self.logger.error(f"Filter matching failed: {str(e)}")
            return False

    async def register_event_handler(self, event_type: str, 
                                   handler: Callable) -> str:
        """Register a handler for specific events."""
        try:
            handler_id = str(uuid.uuid4())
            self.event_handlers[event_type].append({
                'id': handler_id,
                'handler': handler
            })
            return handler_id
            
        except Exception as e:
            self.logger.error(f"Event handler registration failed: {str(e)}")
            return None

    async def trigger_event(self, event_type: str, event_data: Dict) -> bool:
        """Trigger an event and notify all registered handlers."""
        try:
            handlers = self.event_handlers[event_type]
            
            for handler in handlers:
                try:
                    await handler['handler'](event_data)
                except Exception as e:
                    self.logger.error(f"Event handler execution failed: {str(e)}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Event triggering failed: {str(e)}")
            return False

    async def create_session(self, session_id: str = None) -> str:
        """Create a new communication session."""
        try:
            if not session_id:
                session_id = str(uuid.uuid4())
                
            self.active_sessions[session_id] = {
                'created_at': datetime.now(),
                'message_count': 0,
                'last_activity': datetime.now()
            }
            
            return session_id
            
        except Exception as e:
            self.logger.error(f"Session creation failed: {str(e)}")
            return None

    async def get_metrics(self) -> Dict:
        """Get integration layer metrics."""
        try:
            return {
                'message_counts': dict(self.message_stats),
                'queue_sizes': {
                    priority.name: queue.qsize() 
                    for priority, queue in self.message_queues.items()
                },
                'active_sessions': len(self.active_sessions),
                'subscription_counts': {
                    msg_type.name: len(subs) 
                    for msg_type, subs in self.subscriptions.items()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Metrics retrieval failed: {str(e)}")
            return {}

    async def shutdown(self):
        """Clean shutdown of the Integration Layer."""
        try:
            # Cancel message processors
            for processor in self.processors.values():
                processor.cancel()
            
            # Clear queues
            for queue in self.message_queues.values():
                while not queue.empty():
                    await queue.get()
            
            # Clear subscriptions and handlers
            self.subscriptions.clear()
            self.event_handlers.clear()
            
            self.logger.info("Integration Layer shut down successfully")
            
        except Exception as e:
            self.logger.error(f"Shutdown failed: {str(e)}")
