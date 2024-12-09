import asyncio
import aiohttp
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from transformers import pipeline
from collections import defaultdict

class MediaAnalysisAgent:
    """
    Media Analysis Agent for processing news and generating trading signals.
    Includes sentiment analysis, source credibility tracking, and signal generation.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("MediaAnalysisAgent")
        # Sentiment analysis configuration
        self.sentiment_model = pipeline("sentiment-analysis", model="ProsusAI/finbert")
        self.sentiment_threshold = 0.7
        self.momentum_threshold = 0.5
        
        # Source credibility tracking
        self.source_credibility = defaultdict(lambda: 0.5)  # Default credibility of 0.5
        self.source_history = defaultdict(list)
        self.max_history_length = 1000
        
        # Signal generation parameters
        self.signal_validity_period = timedelta(hours=4)
        self.min_sources_required = 3
        
        # Rate limiting and API management
        self.rate_limits = {
            'news_api': 100,  # requests per minute
            'social_api': 50   # requests per minute
        }
        self.api_quotas = defaultdict(int)
        
    async def initialize(self) -> bool:
        """Initialize the agent and required resources."""
        try:
            # Initialize API connections
            self.session = aiohttp.ClientSession()
            
            # Load credibility history
            await self._load_credibility_history()
            
            # Warm up the sentiment model
            _ = self.sentiment_model("warm up text")
            
            self.logger.info("Media Analysis Agent initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Initialization failed: {str(e)}")
            return False
            
    async def process_news_batch(self, news_items: List[Dict]) -> List[Dict]:
        """Process a batch of news items and generate trading signals."""
        try:
            # Group news by symbol
            symbol_news = defaultdict(list)
            for item in news_items:
                symbol_news[item['symbol']].append(item)
            
            # Process each symbol's news
            signals = []
            for symbol, items in symbol_news.items():
                if len(items) >= self.min_sources_required:
                    signal = await self._analyze_symbol_news(symbol, items)
                    if signal:
                        signals.append(signal)
            
            return signals
            
        except Exception as e:
            self.logger.error(f"News batch processing failed: {str(e)}")
            return []
            
    async def _analyze_symbol_news(self, symbol: str, news_items: List[Dict]) -> Optional[Dict]:
        """Analyze news items for a specific symbol and generate a signal if warranted."""
        try:
            # Calculate weighted sentiments
            weighted_sentiments = []
            for item in news_items:
                sentiment_score = await self._calculate_sentiment(item['content'])
                source_weight = self.source_credibility[item['source']]
                weighted_sentiments.append(sentiment_score * source_weight)
            
            # Calculate aggregate sentiment
            if weighted_sentiments:
                avg_sentiment = np.mean(weighted_sentiments)
                sentiment_std = np.std(weighted_sentiments)
                
                # Generate signal if sentiment is strong and consistent
                if abs(avg_sentiment) > self.sentiment_threshold and sentiment_std < 0.3:
                    return {
                        'symbol': symbol,
                        'timestamp': datetime.now(),
                        'signal_type': 'LONG' if avg_sentiment > 0 else 'SHORT',
                        'confidence': min(abs(avg_sentiment), 1.0),
                        'source': 'media_analysis',
                        'expiry': datetime.now() + self.signal_validity_period,
                        'metadata': {
                            'sentiment_score': avg_sentiment,
                            'sentiment_std': sentiment_std,
                            'num_sources': len(news_items)
                        }
                    }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Symbol news analysis failed for {symbol}: {str(e)}")
            return None
            
    async def _calculate_sentiment(self, text: str) -> float:
        """Calculate sentiment score for a piece of text."""
        try:
            # Preprocess text
            cleaned_text = self._preprocess_text(text)
            
            # Get sentiment from model
            result = self.sentiment_model(cleaned_text)[0]
            
            # Convert to normalized score (-1 to 1)
            if result['label'] == 'positive':
                return result['score']
            elif result['label'] == 'negative':
                return -result['score']
            else:
                return 0.0
                
        except Exception as e:
            self.logger.error(f"Sentiment calculation failed: {str(e)}")
            return 0.0
            
    def _preprocess_text(self, text: str) -> str:
        """Clean and prepare text for sentiment analysis."""
        # Basic cleaning
        text = text.replace('\n', ' ').replace('\t', ' ')
        text = ' '.join(text.split())  # Remove extra whitespace
        
        # Truncate if too long
        max_length = 512  # Model's maximum sequence length
        words = text.split()
        if len(words) > max_length:
            text = ' '.join(words[:max_length])
            
        return text
        
    async def update_source_credibility(self, source: str, signal_accuracy: float):
        """Update credibility score for a news source based on signal accuracy."""
        try:
            # Update history
            self.source_history[source].append(signal_accuracy)
            if len(self.source_history[source]) > self.max_history_length:
                self.source_history[source].pop(0)
            
            # Calculate new credibility score
            recent_accuracy = self.source_history[source][-min(100, len(self.source_history[source])):]
            self.source_credibility[source] = np.mean(recent_accuracy)
            
        except Exception as e:
            self.logger.error(f"Credibility update failed for {source}: {str(e)}")
            
    async def _load_credibility_history(self):
        """Load historical credibility data."""
        try:
            # In a real implementation, this would load from a database
            # For now, we'll use default values
            default_sources = {
                'reuters': 0.8,
                'bloomberg': 0.8,
                'wsj': 0.7,
                'seekingalpha': 0.6,
                'twitter': 0.4
            }
            
            for source, score in default_sources.items():
                self.source_credibility[source] = score
                
        except Exception as e:
            self.logger.error(f"Credibility history loading failed: {str(e)}")

    async def shutdown(self):
        """Clean shutdown of the agent."""
        try:
            await self.session.close()
            self.logger.info("Media Analysis Agent shut down successfully")
            
        except Exception as e:
            self.logger.error(f"Shutdown failed: {str(e)}")
