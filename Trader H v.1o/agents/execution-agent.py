import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple
import numpy as np
from collections import deque

class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"
    TRAILING_STOP = "TRAILING_STOP"

class OrderStatus(Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"

class ExecutionStrategy(Enum):
    AGGRESSIVE = "AGGRESSIVE"
    PASSIVE = "PASSIVE"
    SMART = "SMART"
    VWAP = "VWAP"
    TWAP = "TWAP"

@dataclass
class OrderRequest:
    symbol: str
    order_type: OrderType
    direction: str  # 'BUY' or 'SELL'
    quantity: float
    price: Optional[float]
    stop_price: Optional[float]
    time_in_force: str
    strategy: ExecutionStrategy
    metadata: Dict

@dataclass
class OrderUpdate:
    order_id: str
    status: OrderStatus
    filled_quantity: float
    average_price: float
    last_fill_time: datetime
    remaining_quantity: float
    metadata: Dict

class ExecutionAgent:
    """
    Execution Agent for optimal trade execution and order management.
    Includes smart order routing, execution strategy selection, and fill optimization.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("ExecutionAgent")
        
        # Execution Parameters
        self.max_slippage = 0.001  # 10 basis points
        self.min_fill_rate = 0.95  # 95% minimum fill rate
        self.max_spread = 0.002  # 20 basis points maximum spread
        
        # Order Management
        self.active_orders = {}
        self.order_history = {}
        self.fill_statistics = {}
        
        # Performance Tracking
        self.execution_metrics = {
            'slippage': deque(maxlen=1000),
            'fill_rates': deque(maxlen=1000),
            'execution_times': deque(maxlen=1000)
        }
        
        # Market Impact Parameters
        self.impact_threshold = 0.1  # 10% of average volume
        self.spread_multiplier = 1.5
        
    async def initialize(self) -> bool:
        """Initialize the Execution Agent."""
        try:
            # Initialize broker connections
            await self._initialize_broker_connections()
            
            # Load execution statistics
            await self._load_execution_history()
            
            # Initialize market impact models
            await self._initialize_impact_models()
            
            self.logger.info("Execution Agent initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Initialization failed: {str(e)}")
            return False

    async def execute_order(self, request: OrderRequest) -> Tuple[bool, str]:
        """Execute a trade order with optimal execution strategy."""
        try:
            # Validate order parameters
            if not await self._validate_order(request):
                return False, "Order validation failed"
            
            # Select execution strategy
            strategy = await self._select_execution_strategy(request)
            
            # Estimate market impact
            impact = await self._estimate_market_impact(request)
            if impact > self.impact_threshold:
                request = await self._adjust_for_impact(request, impact)
            
            # Generate order parameters
            order_params = await self._generate_order_parameters(request, strategy)
            
            # Place order
            order_id = await self._place_order(order_params)
            if not order_id:
                return False, "Order placement failed"
            
            # Initialize order tracking
            await self._initialize_order_tracking(order_id, request)
            
            return True, order_id
            
        except Exception as e:
            self.logger.error(f"Order execution failed: {str(e)}")
            return False, str(e)

    async def monitor_order(self, order_id: str) -> OrderUpdate:
        """Monitor the status of an active order."""
        try:
            if order_id not in self.active_orders:
                raise ValueError(f"Order {order_id} not found")
            
            # Get order status
            status = await self._get_order_status(order_id)
            
            # Update execution metrics
            await self._update_execution_metrics(order_id, status)
            
            # Check for execution quality issues
            if await self._check_execution_issues(order_id, status):
                await self._handle_execution_issues(order_id)
            
            return status
            
        except Exception as e:
            self.logger.error(f"Order monitoring failed: {str(e)}")
            return None

    async def _select_execution_strategy(self, request: OrderRequest) -> ExecutionStrategy:
        """Select optimal execution strategy based on order and market conditions."""
        try:
            # Get market conditions
            volatility = await self._get_market_volatility(request.symbol)
            liquidity = await self._get_market_liquidity(request.symbol)
            spread = await self._get_market_spread(request.symbol)
            
            # Calculate strategy scores
            scores = {
                ExecutionStrategy.AGGRESSIVE: self._score_aggressive_strategy(
                    request, volatility, liquidity, spread
                ),
                ExecutionStrategy.PASSIVE: self._score_passive_strategy(
                    request, volatility, liquidity, spread
                ),
                ExecutionStrategy.SMART: self._score_smart_strategy(
                    request, volatility, liquidity, spread
                ),
                ExecutionStrategy.VWAP: self._score_vwap_strategy(
                    request, volatility, liquidity, spread
                ),
                ExecutionStrategy.TWAP: self._score_twap_strategy(
                    request, volatility, liquidity, spread
                )
            }
            
            return max(scores.items(), key=lambda x: x[1])[0]
            
        except Exception as e:
            self.logger.error(f"Strategy selection failed: {str(e)}")
            return ExecutionStrategy.SMART

    async def _generate_order_parameters(self, request: OrderRequest, 
                                      strategy: ExecutionStrategy) -> Dict:
        """Generate detailed order parameters based on selected strategy."""
        try:
            base_params = {
                'symbol': request.symbol,
                'quantity': request.quantity,
                'direction': request.direction,
                'order_type': request.order_type,
                'time_in_force': request.time_in_force
            }
            
            if strategy == ExecutionStrategy.AGGRESSIVE:
                return await self._generate_aggressive_params(base_params, request)
            elif strategy == ExecutionStrategy.PASSIVE:
                return await self._generate_passive_params(base_params, request)
            elif strategy == ExecutionStrategy.VWAP:
                return await self._generate_vwap_params(base_params, request)
            elif strategy == ExecutionStrategy.TWAP:
                return await self._generate_twap_params(base_params, request)
            else:  # SMART strategy
                return await self._generate_smart_params(base_params, request)
                
        except Exception as e:
            self.logger.error(f"Order parameter generation failed: {str(e)}")
            return None

    async def _estimate_market_impact(self, request: OrderRequest) -> float:
        """Estimate market impact of the order."""
        try:
            # Get market data
            avg_volume = await self._get_average_volume(request.symbol)
            volatility = await self._get_market_volatility(request.symbol)
            spread = await self._get_market_spread(request.symbol)
            
            # Calculate impact factors
            volume_factor = request.quantity / avg_volume
            volatility_factor = volatility / 0.2  # Normalized to 20% volatility
            spread_factor = spread / self.max_spread
            
            # Combine factors
            impact = (
                volume_factor * 0.5 +
                volatility_factor * 0.3 +
                spread_factor * 0.2
            )
            
            return impact
            
        except Exception as e:
            self.logger.error(f"Market impact estimation failed: {str(e)}")
            return float('inf')

    async def _handle_execution_issues(self, order_id: str):
        """Handle execution quality issues."""
        try:
            order = self.active_orders[order_id]
            status = await self._get_order_status(order_id)
            
            if status.status == OrderStatus.PARTIALLY_FILLED:
                if await self._should_adjust_order(order_id):
                    await self._adjust_order_parameters(order_id)
                    
            elif status.status == OrderStatus.ACTIVE:
                if await self._is_order_stale(order_id):
                    await self._cancel_and_resubmit(order_id)
                    
            await self._update_execution_statistics(order_id)
            
        except Exception as e:
            self.logger.error(f"Execution issue handling failed: {str(e)}")

    async def _adjust_order_parameters(self, order_id: str):
        """Adjust order parameters based on execution performance."""
        try:
            order = self.active_orders[order_id]
            market_data = await self._get_market_data(order.symbol)
            
            # Calculate new parameters
            new_price = await self._calculate_adjusted_price(order, market_data)
            new_quantity = await self._calculate_adjusted_quantity(order, market_data)
            
            # Update order
            update_successful = await self._update_order(
                order_id, new_price, new_quantity
            )
            
            if update_successful:
                self.logger.info(f"Order {order_id} parameters adjusted successfully")
                
        except Exception as e:
            self.logger.error(f"Order parameter adjustment failed: {str(e)}")

    async def _update_execution_metrics(self, order_id: str, status: OrderUpdate):
        """Update execution quality metrics."""
        try:
            order = self.active_orders[order_id]
            
            # Calculate metrics
            slippage = self._calculate_slippage(order, status)
            fill_rate = status.filled_quantity / order.quantity
            execution_time = (status.last_fill_time - order.submission_time).total_seconds()
            
            # Update metrics
            self.execution_metrics['slippage'].append(slippage)
            self.execution_metrics['fill_rates'].append(fill_rate)
            self.execution_metrics['execution_times'].append(execution_time)
            
            # Log significant deviations
            if slippage > self.max_slippage:
                self.logger.warning(f"High slippage detected for order {order_id}: {slippage}")
                
        except Exception as e:
            self.logger.error(f"Metrics update failed: {str(e)}")

    async def shutdown(self):
        """Clean shutdown of the agent."""
        try:
            # Cancel all active orders
            for order_id in list(self.active_orders.keys()):
                await self._cancel_order(order_id)
            
            # Save execution statistics
            await self._save_execution_statistics()
            
            # Close connections
            await self._close_broker_connections()
            
            self.logger.info("Execution Agent shut down successfully")
            
        except Exception as e:
            self.logger.error(f"Shutdown failed: {str(e)}")
