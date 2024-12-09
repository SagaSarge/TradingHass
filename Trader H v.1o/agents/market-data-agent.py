import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
import asyncio
from dataclasses import dataclass
from enum import Enum
import talib

@dataclass
class MarketData:
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    vwap: float
    trades: int
    
class TimeFrame(Enum):
    M1 = "1min"
    M5 = "5min"
    M15 = "15min"
    H1 = "1hour"
    H4 = "4hour"
    D1 = "1day"

class MarketDataAgent:
    """
    Market Data Agent for technical analysis and price action signals.
    Includes multi-timeframe analysis, volume profiling, and pattern recognition.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("MarketDataAgent")
        
        # Technical Analysis Parameters
        self.timeframes = [
            TimeFrame.M5,
            TimeFrame.M15,
            TimeFrame.H1,
            TimeFrame.H4
        ]
        
        # Indicator Parameters
        self.indicator_params = {
            'RSI': {'period': 14, 'overbought': 70, 'oversold': 30},
            'MACD': {'fast': 12, 'slow': 26, 'signal': 9},
            'BB': {'period': 20, 'std': 2},
            'ATR': {'period': 14},
            'ADX': {'period': 14, 'threshold': 25}
        }
        
        # Initialize data storage
        self.price_history = {}
        self.volume_profile = {}
        self.indicator_cache = {}
        
    async def initialize(self) -> bool:
        """Initialize the Market Data Agent."""
        try:
            # Initialize price history databases
            for timeframe in self.timeframes:
                self.price_history[timeframe] = {}
                self.indicator_cache[timeframe] = {}
            
            self.logger.info("Market Data Agent initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Initialization failed: {str(e)}")
            return False

    async def process_market_data(self, data: MarketData) -> List[Dict]:
        """Process new market data and generate signals."""
        try:
            # Update price history
            await self._update_price_history(data)
            
            # Generate signals
            signals = []
            
            # Technical analysis signals
            ta_signals = await self._generate_technical_signals(data.symbol)
            signals.extend(ta_signals)
            
            # Volume analysis signals
            vol_signals = await self._analyze_volume_patterns(data)
            signals.extend(vol_signals)
            
            # Price action signals
            price_signals = await self._analyze_price_action(data)
            signals.extend(price_signals)
            
            return signals
            
        except Exception as e:
            self.logger.error(f"Market data processing failed: {str(e)}")
            return []

    async def _generate_technical_signals(self, symbol: str) -> List[Dict]:
        """Generate signals based on technical indicators."""
        try:
            signals = []
            
            for timeframe in self.timeframes:
                if symbol not in self.price_history[timeframe]:
                    continue
                
                df = self.price_history[timeframe][symbol]
                
                # Calculate indicators
                rsi = self._calculate_rsi(df)
                macd, signal, hist = self._calculate_macd(df)
                upper, middle, lower = self._calculate_bollinger_bands(df)
                adx = self._calculate_adx(df)
                
                # RSI signals
                if rsi[-1] < self.indicator_params['RSI']['oversold']:
                    signals.append(self._create_signal(
                        symbol, 'RSI_OVERSOLD', 'LONG', 
                        confidence=0.7,
                        timeframe=timeframe,
                        metadata={'rsi': rsi[-1]}
                    ))
                elif rsi[-1] > self.indicator_params['RSI']['overbought']:
                    signals.append(self._create_signal(
                        symbol, 'RSI_OVERBOUGHT', 'SHORT',
                        confidence=0.7,
                        timeframe=timeframe,
                        metadata={'rsi': rsi[-1]}
                    ))
                
                # MACD signals
                if hist[-1] > 0 and hist[-2] <= 0:
                    signals.append(self._create_signal(
                        symbol, 'MACD_CROSSOVER', 'LONG',
                        confidence=0.6,
                        timeframe=timeframe,
                        metadata={'macd': macd[-1], 'signal': signal[-1]}
                    ))
                elif hist[-1] < 0 and hist[-2] >= 0:
                    signals.append(self._create_signal(
                        symbol, 'MACD_CROSSOVER', 'SHORT',
                        confidence=0.6,
                        timeframe=timeframe,
                        metadata={'macd': macd[-1], 'signal': signal[-1]}
                    ))
                
                # Bollinger Band signals
                close = df['close'].iloc[-1]
                if close < lower[-1]:
                    signals.append(self._create_signal(
                        symbol, 'BB_OVERSOLD', 'LONG',
                        confidence=0.65,
                        timeframe=timeframe,
                        metadata={'bb_lower': lower[-1], 'price': close}
                    ))
                elif close > upper[-1]:
                    signals.append(self._create_signal(
                        symbol, 'BB_OVERBOUGHT', 'SHORT',
                        confidence=0.65,
                        timeframe=timeframe,
                        metadata={'bb_upper': upper[-1], 'price': close}
                    ))
                
            return signals
            
        except Exception as e:
            self.logger.error(f"Technical signal generation failed: {str(e)}")
            return []

    async def _analyze_volume_patterns(self, data: MarketData) -> List[Dict]:
        """Analyze volume patterns and generate signals."""
        try:
            signals = []
            
            # Calculate volume profile
            volume_profile = self._update_volume_profile(data)
            
            # Volume spike detection
            avg_volume = np.mean([bar.volume for bar in self.price_history[TimeFrame.M5][data.symbol][-20:]])
            if data.volume > avg_volume * 2:
                signals.append(self._create_signal(
                    data.symbol, 'VOLUME_SPIKE', 
                    'LONG' if data.close > data.open else 'SHORT',
                    confidence=0.6,
                    timeframe=TimeFrame.M5,
                    metadata={'volume_ratio': data.volume / avg_volume}
                ))
            
            # Volume trend analysis
            volume_trend = self._calculate_volume_trend(data.symbol)
            if abs(volume_trend) > 0.5:
                signals.append(self._create_signal(
                    data.symbol, 'VOLUME_TREND',
                    'LONG' if volume_trend > 0 else 'SHORT',
                    confidence=abs(volume_trend),
                    timeframe=TimeFrame.M5,
                    metadata={'trend_strength': volume_trend}
                ))
            
            return signals
            
        except Exception as e:
            self.logger.error(f"Volume pattern analysis failed: {str(e)}")
            return []

    async def _analyze_price_action(self, data: MarketData) -> List[Dict]:
        """Analyze price action patterns and generate signals."""
        try:
            signals = []
            
            # Candlestick patterns
            patterns = self._identify_candlestick_patterns(data)
            for pattern in patterns:
                signals.append(self._create_signal(
                    data.symbol, f'CANDLESTICK_{pattern["name"]}',
                    pattern["direction"],
                    confidence=pattern["strength"],
                    timeframe=TimeFrame.M5,
                    metadata={'pattern': pattern["name"]}
                ))
            
            # Support/Resistance levels
            levels = self._calculate_support_resistance(data.symbol)
            for level in levels:
                if abs(data.close - level) / data.close < 0.001:  # Within 0.1%
                    signals.append(self._create_signal(
                        data.symbol, 'SUPPORT_RESISTANCE',
                        'LONG' if data.close > level else 'SHORT',
                        confidence=0.7,
                        timeframe=TimeFrame.M5,
                        metadata={'level': level}
                    ))
            
            return signals
            
        except Exception as e:
            self.logger.error(f"Price action analysis failed: {str(e)}")
            return []

    def _calculate_rsi(self, df: pd.DataFrame) -> np.ndarray:
        """Calculate RSI indicator."""
        return talib.RSI(df['close'].values, timeperiod=self.indicator_params['RSI']['period'])

    def _calculate_macd(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Calculate MACD indicator."""
        return talib.MACD(
            df['close'].values,
            fastperiod=self.indicator_params['MACD']['fast'],
            slowperiod=self.indicator_params['MACD']['slow'],
            signalperiod=self.indicator_params['MACD']['signal']
        )

    def _calculate_bollinger_bands(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Calculate Bollinger Bands."""
        return talib.BBANDS(
            df['close'].values,
            timeperiod=self.indicator_params['BB']['period'],
            nbdevup=self.indicator_params['BB']['std'],
            nbdevdn=self.indicator_params['BB']['std']
        )

    def _calculate_adx(self, df: pd.DataFrame) -> np.ndarray:
        """Calculate ADX indicator."""
        return talib.ADX(
            df['high'].values,
            df['low'].values,
            df['close'].values,
            timeperiod=self.indicator_params['ADX']['period']
        )

    def _create_signal(self, symbol: str, signal_type: str, direction: str,
                      confidence: float, timeframe: TimeFrame, metadata: Dict) -> Dict:
        """Create a standardized signal dictionary."""
        return {
            'symbol': symbol,
            'timestamp': datetime.now(),
            'signal_type': signal_type,
            'direction': direction,
            'confidence': confidence,
            'timeframe': timeframe.value,
            'metadata': metadata
        }

    async def shutdown(self):
        """Clean shutdown of the agent."""
        try:
            # Save any necessary data
            await self._save_historical_data()
            self.logger.info("Market Data Agent shut down successfully")
            
        except Exception as e:
            self.logger.error(f"Shutdown failed: {str(e)}")
