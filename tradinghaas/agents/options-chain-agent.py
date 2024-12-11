import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
import asyncio
from scipy.stats import norm

@dataclass
class OptionsData:
    symbol: str
    strike: float
    expiration: datetime
    option_type: str  # 'CALL' or 'PUT'
    bid: float
    ask: float
    volume: int
    open_interest: int
    implied_volatility: float
    delta: float
    gamma: float
    theta: float
    vega: float
    underlying_price: float

class OptionsChainAgent:
    """
    Options Chain Agent for analyzing options flow and generating trading signals.
    Includes unusual activity detection, Greeks analysis, and flow-based signals.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("OptionsChainAgent")
        
        # Flow analysis parameters
        self.flow_threshold = 2.0  # Standard deviations for unusual flow
        self.min_option_volume = 100
        self.min_dollar_value = 50000
        
        # Options chain tracking
        self.historical_flow = {}
        self.volume_patterns = defaultdict(list)
        self.unusual_activity = defaultdict(list)
        
        # Greeks thresholds
        self.delta_threshold = 0.3
        self.gamma_threshold = 0.1
        self.unusual_iv_threshold = 2.0
        
    async def initialize(self) -> bool:
        """Initialize the Options Chain Agent."""
        try:
            # Initialize historical data structures
            await self._initialize_historical_data()
            
            # Set up statistical models
            await self._initialize_models()
            
            self.logger.info("Options Chain Agent initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Initialization failed: {str(e)}")
            return False

    async def process_options_data(self, options_chain: List[OptionsData]) -> List[Dict]:
        """Process options chain data and generate trading signals."""
        try:
            # Group options by symbol
            symbol_options = self._group_by_symbol(options_chain)
            
            signals = []
            for symbol, options in symbol_options.items():
                # Analyze unusual activity
                unusual_signals = await self._detect_unusual_activity(options)
                if unusual_signals:
                    signals.extend(unusual_signals)
                
                # Analyze options flow
                flow_signals = await self._analyze_options_flow(options)
                if flow_signals:
                    signals.extend(flow_signals)
                
                # Analyze Greeks patterns
                greek_signals = await self._analyze_greeks_patterns(options)
                if greek_signals:
                    signals.extend(greek_signals)
            
            return signals
            
        except Exception as e:
            self.logger.error(f"Options data processing failed: {str(e)}")
            return []

    async def _detect_unusual_activity(self, options: List[OptionsData]) -> List[Dict]:
        """Detect unusual options activity based on volume and price patterns."""
        try:
            signals = []
            
            for option in options:
                # Calculate dollar value of activity
                dollar_value = option.volume * (option.bid + option.ask) / 2 * 100
                
                if dollar_value >= self.min_dollar_value:
                    # Calculate historical average volume
                    avg_volume = self._get_average_volume(option)
                    volume_std = self._get_volume_std(option)
                    
                    # Check for unusual volume
                    if volume_std > 0:
                        z_score = (option.volume - avg_volume) / volume_std
                        
                        if abs(z_score) > self.flow_threshold:
                            signal = {
                                'symbol': option.symbol,
                                'timestamp': datetime.now(),
                                'signal_type': 'UNUSUAL_ACTIVITY',
                                'direction': 'LONG' if option.option_type == 'CALL' else 'SHORT',
                                'confidence': min(abs(z_score) / self.flow_threshold, 1.0),
                                'metadata': {
                                    'strike': option.strike,
                                    'expiration': option.expiration,
                                    'volume': option.volume,
                                    'dollar_value': dollar_value,
                                    'z_score': z_score
                                }
                            }
                            signals.append(signal)
            
            return signals
            
        except Exception as e:
            self.logger.error(f"Unusual activity detection failed: {str(e)}")
            return []

    async def _analyze_options_flow(self, options: List[OptionsData]) -> List[Dict]:
        """Analyze options flow patterns and generate signals."""
        try:
            signals = []
            
            # Group by expiration
            exp_groups = self._group_by_expiration(options)
            
            for exp_date, exp_options in exp_groups.items():
                # Calculate put-call ratio
                put_call_ratio = self._calculate_put_call_ratio(exp_options)
                
                # Calculate flow intensity
                flow_intensity = self._calculate_flow_intensity(exp_options)
                
                # Generate signals based on flow patterns
                if abs(flow_intensity) > self.flow_threshold:
                    signal = {
                        'symbol': exp_options[0].symbol,
                        'timestamp': datetime.now(),
                        'signal_type': 'OPTIONS_FLOW',
                        'direction': 'LONG' if flow_intensity > 0 else 'SHORT',
                        'confidence': min(abs(flow_intensity) / self.flow_threshold, 1.0),
                        'metadata': {
                            'expiration': exp_date,
                            'put_call_ratio': put_call_ratio,
                            'flow_intensity': flow_intensity
                        }
                    }
                    signals.append(signal)
            
            return signals
            
        except Exception as e:
            self.logger.error(f"Options flow analysis failed: {str(e)}")
            return []

    async def _analyze_greeks_patterns(self, options: List[OptionsData]) -> List[Dict]:
        """Analyze options Greeks patterns for potential signals."""
        try:
            signals = []
            
            # Calculate aggregate Greeks exposure
            total_delta = sum(opt.delta * opt.volume for opt in options)
            total_gamma = sum(opt.gamma * opt.volume for opt in options)
            
            # Check for significant Greeks imbalances
            if abs(total_delta) > self.delta_threshold or abs(total_gamma) > self.gamma_threshold:
                signal = {
                    'symbol': options[0].symbol,
                    'timestamp': datetime.now(),
                    'signal_type': 'GREEKS_EXPOSURE',
                    'direction': 'LONG' if total_delta > 0 else 'SHORT',
                    'confidence': min(max(abs(total_delta), abs(total_gamma)), 1.0),
                    'metadata': {
                        'total_delta': total_delta,
                        'total_gamma': total_gamma
                    }
                }
                signals.append(signal)
            
            return signals
            
        except Exception as e:
            self.logger.error(f"Greeks pattern analysis failed: {str(e)}")
            return []

    def _calculate_implied_volatility(self, option: OptionsData) -> float:
        """Calculate implied volatility using Newton-Raphson method."""
        try:
            # Implementation of Newton-Raphson method for IV calculation
            r = 0.02  # Risk-free rate
            S = option.underlying_price
            K = option.strike
            T = (option.expiration - datetime.now()).days / 365.0
            mid_price = (option.bid + option.ask) / 2
            
            def black_scholes(S, K, T, r, sigma, option_type):
                d1 = (np.log(S/K) + (r + sigma**2/2)*T) / (sigma*np.sqrt(T))
                d2 = d1 - sigma*np.sqrt(T)
                
                if option_type == 'CALL':
                    return S*norm.cdf(d1) - K*np.exp(-r*T)*norm.cdf(d2)
                else:
                    return K*np.exp(-r*T)*norm.cdf(-d2) - S*norm.cdf(-d1)
            
            # Newton-Raphson iteration
            sigma = 0.5  # Initial guess
            for _ in range(100):
                price = black_scholes(S, K, T, r, sigma, option.option_type)
                diff = mid_price - price
                if abs(diff) < 0.0001:
                    break
                vega = S*np.sqrt(T)*norm.pdf(d1)
                sigma = sigma + diff/vega
            
            return sigma
            
        except Exception as e:
            self.logger.error(f"IV calculation failed: {str(e)}")
            return 0.0

    def _group_by_symbol(self, options: List[OptionsData]) -> Dict[str, List[OptionsData]]:
        """Group options data by symbol."""
        grouped = defaultdict(list)
        for option in options:
            grouped[option.symbol].append(option)
        return grouped

    def _group_by_expiration(self, options: List[OptionsData]) -> Dict[datetime, List[OptionsData]]:
        """Group options by expiration date."""
        grouped = defaultdict(list)
        for option in options:
            grouped[option.expiration].append(option)
        return grouped

    def _calculate_put_call_ratio(self, options: List[OptionsData]) -> float:
        """Calculate put-call ratio for a group of options."""
        call_volume = sum(opt.volume for opt in options if opt.option_type == 'CALL')
        put_volume = sum(opt.volume for opt in options if opt.option_type == 'PUT')
        return put_volume / call_volume if call_volume > 0 else float('inf')

    def _calculate_flow_intensity(self, options: List[OptionsData]) -> float:
        """Calculate the intensity of options flow."""
        call_flow = sum(opt.volume * opt.delta for opt in options if opt.option_type == 'CALL')
        put_flow = sum(opt.volume * opt.delta for opt in options if opt.option_type == 'PUT')
        return call_flow - put_flow

    async def shutdown(self):
        """Clean shutdown of the agent."""
        try:
            # Save historical data
            await self._save_historical_data()
            self.logger.info("Options Chain Agent shut down successfully")
            
        except Exception as e:
            self.logger.error(f"Shutdown failed: {str(e)}")
