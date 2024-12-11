import redis
import json

class TradingSystemCore:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.subscribed_channels = []

    def subscribe_to_market_data(self, ticker):
        """Subscribe to market data for a specific ticker."""
        channel = f"market-data:{ticker}"
        self.subscribed_channels.append(channel)
        pubsub = self.redis_client.pubsub()
        pubsub.subscribe(channel)
        print(f"Subscribed to channel: {channel}")
        for message in pubsub.listen():
            if message["type"] == "message":
                market_data = json.loads(message["data"])
                print(f"Processing market data for {ticker}: {market_data}")
                self.process_market_data(market_data, ticker)

    def process_market_data(self, data, ticker):
        """Processes market data."""
        print(f"Executing trading logic based on data for {ticker}...")
        # Add custom trading logic here

# Example usage
if __name__ == "__main__":
    core = TradingSystemCore()
    ticker = "AAPL"
    core.subscribe_to_market_data(ticker)
