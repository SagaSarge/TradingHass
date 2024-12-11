from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import logging
import asyncio
from datetime import datetime

class BaseAgent(ABC):
    """Abstract base class for all trading system agents"""
    
    def __init__(self, name: str, priority: int):
        self.name = name
        self.priority = priority
        self.active = False
        self.last_error = None
        self.metrics = {}
        self._logger = logging.getLogger(f"agent.{name}")

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize agent resources and connections"""
        pass

    @abstractmethod
    async def process(self, data: Dict) -> Dict:
        """Process incoming data and generate results"""
        pass

    @abstractmethod
    async def shutdown(self) -> bool:
        """Clean shutdown of agent resources"""
        pass

class AgentSystem:
    """Manages the lifecycle and coordination of all agents"""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.message_queue = asyncio.Queue()
        self.error_handler = ErrorHandler()
        self._logger = logging.getLogger("agent_system")

    async def register_agent(self, agent: BaseAgent) -> bool:
        """Register a new agent with the system"""
        try:
            if await agent.initialize():
                self.agents[agent.name] = agent
                self._logger.info(f"Agent {agent.name} registered successfully")
                return True
            return False
        except Exception as e:
            self._logger.error(f"Failed to register agent {agent.name}: {str(e)}")
            return False

class MediaAnalysisAgent(BaseAgent):
    """Processes news and sentiment data"""
    
    def __init__(self):
        super().__init__("media_analysis", priority=1)
        self.sentiment_threshold = 0.7
        self.credibility_scores = {}

    async def process(self, data: Dict) -> Dict:
        """Process news data and generate sentiment signals"""
        try:
            # Process news content
            sentiment_score = await self._analyze_sentiment(data['content'])
            credibility = await self._assess_credibility(data['source'])
            
            return {
                'timestamp': datetime.now(),
                'sentiment': sentiment_score,
                'credibility': credibility,
                'signal_strength': sentiment_score * credibility
            }
        except Exception as e:
            self._logger.error(f"Error processing media data: {str(e)}")
            raise

class OptionsChainAgent(BaseAgent):
    """Analyzes options flow and unusual activity"""
    
    def __init__(self):
        super().__init__("options_chain", priority=1)
        self.flow_threshold = 2.0
        self.volatility_threshold = 0.3

    async def process(self, data: Dict) -> Dict:
        """Process options chain data and detect unusual activity"""
        try:
            flow_score = await self._analyze_flow(data['options_chain'])
            unusual_activity = await self._detect_unusual_activity(data['volume'])
            
            return {
                'timestamp': datetime.now(),
                'flow_score': flow_score,
                'unusual_activity': unusual_activity,
                'alert_level': self._calculate_alert_level(flow_score, unusual_activity)
            }
        except Exception as e:
            self._logger.error(f"Error processing options data: {str(e)}")
            raise

class RiskManagementAgent(BaseAgent):
    """Manages system-wide risk and position sizing"""
    
    def __init__(self):
        super().__init__("risk_management", priority=0)  # Highest priority
        self.max_position_size = 0.02  # 2% max position size
        self.max_portfolio_risk = 0.05  # 5% max portfolio risk

    async def process(self, data: Dict) -> Dict:
        """Process risk metrics and generate risk signals"""
        try:
            position_risk = await self._calculate_position_risk(data)
            portfolio_risk = await self._calculate_portfolio_risk()
            
            return {
                'timestamp': datetime.now(),
                'position_approved': position_risk <= self.max_position_size,
                'portfolio_risk': portfolio_risk,
                'risk_level': self._calculate_risk_level(position_risk, portfolio_risk)
            }
        except Exception as e:
            self._logger.error(f"Error processing risk data: {str(e)}")
            raise

class ErrorHandler:
    """Centralized error handling and recovery system"""
    
    def __init__(self):
        self.error_log = []
        self._logger = logging.getLogger("error_handler")

    async def handle_error(self, error: Exception, source: str, severity: int) -> bool:
        """Handle system errors and initiate recovery if needed"""
        try:
            error_entry = {
                'timestamp': datetime.now(),
                'source': source,
                'severity': severity,
                'error': str(error)
            }
            
            self.error_log.append(error_entry)
            
            if severity == 1:  # Critical error
                await self._initiate_emergency_protocol(error_entry)
            
            return await self._attempt_recovery(error_entry)
        except Exception as e:
            self._logger.critical(f"Error handler failure: {str(e)}")
            return False
