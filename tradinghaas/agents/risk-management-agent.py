from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import logging
from enum import Enum
import asyncio

class RiskLevel(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

@dataclass
class Position:
    symbol: str
    direction: str  # 'LONG' or 'SHORT'
    quantity: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    timestamp: datetime
    metadata: Dict

@dataclass
class PortfolioState:
    total_value: float
    cash: float
    positions: Dict[str, Position]
    risk_exposure: float
    margin_used: float
    margin_available: float

class RiskManagementAgent:
    """
    Risk Management Agent for portfolio risk control and position sizing.
    Includes position management, risk assessment, and portfolio monitoring.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("RiskManagementAgent")
        
        # Risk Parameters
        self.max_position_size = 0.02  # 2% max position size
        self.max_portfolio_risk = 0.05  # 5% max portfolio risk
        self.max_correlation = 0.7  # Maximum correlation between positions
        self.max_sector_exposure = 0.25  # 25% max sector exposure
        
        # Portfolio Limits
        self.max_leverage = 2.0
        self.margin_minimum = 0.3  # 30% minimum margin requirement
        self.emergency_cash_buffer = 0.1  # 10% emergency cash buffer
        
        # Risk Metrics
        self.var_confidence = 0.95  # 95% VaR confidence level
        self.var_window = 252  # One year of trading days
        self.stress_test_scenarios = self._initialize_stress_scenarios()
        
        # Position tracking
        self.positions = {}
        self.historical_positions = {}
        self.risk_metrics = {}
        
    async def initialize(self) -> bool:
        """Initialize the Risk Management Agent."""
        try:
            # Initialize risk monitoring systems
            await self._initialize_risk_monitoring()
            
            # Load historical data
            await self._load_historical_data()
            
            # Initialize correlation matrix
            await self._initialize_correlation_matrix()
            
            self.logger.info("Risk Management Agent initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Initialization failed: {str(e)}")
            return False

    async def validate_trade(self, signal: Dict, portfolio: PortfolioState) -> Tuple[bool, Dict]:
        """Validate a potential trade against risk parameters."""
        try:
            symbol = signal['symbol']
            direction = signal['direction']
            
            # Calculate position size
            position_size = await self._calculate_position_size(signal, portfolio)
            
            # Check risk limits
            risk_checks = await self._perform_risk_checks(symbol, direction, position_size, portfolio)
            
            if not all(risk_checks.values()):
                return False, {
                    'reason': 'Risk limits exceeded',
                    'failed_checks': [k for k, v in risk_checks.items() if not v]
                }
            
            # Calculate trade parameters
            trade_params = {
                'position_size': position_size,
                'risk_level': await self._calculate_risk_level(signal, portfolio),
                'stop_loss': await self._calculate_stop_loss(signal),
                'take_profit': await self._calculate_take_profit(signal)
            }
            
            return True, trade_params
            
        except Exception as e:
            self.logger.error(f"Trade validation failed: {str(e)}")
            return False, {'reason': 'Validation error'}

    async def _calculate_position_size(self, signal: Dict, portfolio: PortfolioState) -> float:
        """Calculate appropriate position size based on risk parameters."""
        try:
            # Get base position size from portfolio value
            base_size = portfolio.total_value * self.max_position_size
            
            # Adjust for signal confidence
            confidence_factor = signal.get('confidence', 0.5)
            adjusted_size = base_size * confidence_factor
            
            # Adjust for market volatility
            volatility_factor = await self._calculate_volatility_factor(signal['symbol'])
            adjusted_size *= volatility_factor
            
            # Adjust for correlation with existing positions
            correlation_factor = await self._calculate_correlation_factor(signal['symbol'], portfolio)
            adjusted_size *= correlation_factor
            
            return min(adjusted_size, base_size)
            
        except Exception as e:
            self.logger.error(f"Position size calculation failed: {str(e)}")
            return 0.0

    async def _perform_risk_checks(self, symbol: str, direction: str, 
                                 position_size: float, portfolio: PortfolioState) -> Dict[str, bool]:
        """Perform comprehensive risk checks."""
        try:
            return {
                'portfolio_risk': await self._check_portfolio_risk(portfolio),
                'position_limit': await self._check_position_limit(position_size, portfolio),
                'sector_exposure': await self._check_sector_exposure(symbol, position_size, portfolio),
                'correlation_risk': await self._check_correlation_risk(symbol, portfolio),
                'leverage_limit': await self._check_leverage_limit(position_size, portfolio),
                'margin_requirement': await self._check_margin_requirement(position_size, portfolio),
                'liquidity_risk': await self._check_liquidity_risk(symbol, position_size)
            }
            
        except Exception as e:
            self.logger.error(f"Risk checks failed: {str(e)}")
            return {'error': False}

    async def calculate_portfolio_risk(self, portfolio: PortfolioState) -> Dict:
        """Calculate comprehensive portfolio risk metrics."""
        try:
            risk_metrics = {
                'var': await self._calculate_value_at_risk(portfolio),
                'beta': await self._calculate_portfolio_beta(portfolio),
                'sharpe_ratio': await self._calculate_sharpe_ratio(portfolio),
                'max_drawdown': await self._calculate_max_drawdown(portfolio),
                'correlation_matrix': await self._update_correlation_matrix(portfolio),
                'stress_test_results': await self._run_stress_tests(portfolio)
            }
            
            self.risk_metrics = risk_metrics
            return risk_metrics
            
        except Exception as e:
            self.logger.error(f"Portfolio risk calculation failed: {str(e)}")
            return {}

    async def _calculate_value_at_risk(self, portfolio: PortfolioState) -> float:
        """Calculate Value at Risk using historical simulation."""
        try:
            returns = []
            for symbol, position in portfolio.positions.items():
                hist_returns = await self._get_historical_returns(symbol)
                weighted_returns = hist_returns * position.quantity * position.current_price
                returns.append(weighted_returns)
            
            portfolio_returns = np.sum(returns, axis=0)
            var = np.percentile(portfolio_returns, (1 - self.var_confidence) * 100)
            
            return abs(var)
            
        except Exception as e:
            self.logger.error(f"VaR calculation failed: {str(e)}")
            return float('inf')

    async def _run_stress_tests(self, portfolio: PortfolioState) -> Dict:
        """Run stress test scenarios on the portfolio."""
        try:
            results = {}
            for scenario, params in self.stress_test_scenarios.items():
                scenario_pnl = 0
                for symbol, position in portfolio.positions.items():
                    price_change = params.get('price_change', 0)
                    vol_change = params.get('volatility_change', 0)
                    scenario_pnl += self._calculate_scenario_pnl(position, price_change, vol_change)
                
                results[scenario] = {
                    'pnl': scenario_pnl,
                    'pnl_percentage': scenario_pnl / portfolio.total_value
                }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Stress testing failed: {str(e)}")
            return {}

    def _initialize_stress_scenarios(self) -> Dict:
        """Initialize stress test scenarios."""
        return {
            'market_crash': {
                'price_change': -0.15,
                'volatility_change': 2.0
            },
            'sector_rotation': {
                'price_change': -0.08,
                'volatility_change': 1.5
            },
            'volatility_spike': {
                'price_change': -0.05,
                'volatility_change': 3.0
            }
        }

    async def update_position(self, symbol: str, price: float, quantity: float = None):
        """Update position information and risk metrics."""
        try:
            if symbol in self.positions:
                position = self.positions[symbol]
                position.current_price = price
                if quantity is not None:
                    position.quantity = quantity
                
                position.unrealized_pnl = (
                    (price - position.entry_price) * position.quantity
                    if position.direction == 'LONG'
                    else (position.entry_price - price) * position.quantity
                )
                
                # Update risk metrics
                await self._update_risk_metrics(symbol)
                
        except Exception as e:
            self.logger.error(f"Position update failed: {str(e)}")

    async def shutdown(self):
        """Clean shutdown of the agent."""
        try:
            # Save position and risk data
            await self._save_historical_data()
            self.logger.info("Risk Management Agent shut down successfully")
            
        except Exception as e:
            self.logger.error(f"Shutdown failed: {str(e)}")
