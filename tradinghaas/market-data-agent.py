import os
import redis
import time
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path="./.env")

# Polygon API Key from .env
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
if not POLYGON_API_KEY:
    raise Exception("POLYGON_API_KEY not found in .env file!")

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_CHANNEL = os.getenv("REDIS_CHANNEL", "market-data")

# Polygon API URL
BASE_URL = "https://api.polygon.io/v2/aggs/ticker"

# Connect to Redis
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)

def fetch_market_data(ticker, interval="1min", limit=1):
    """
    Fetch market data for a specific ticker from the Polygon API.
    """
    url = f"{BASE_URL}/{ticker}/prev?apiKey={POLYGON_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching data for {ticker}: {response.status_code} - {response.text}")
        return None

def publish_to_redis(channel, data):
    """
    Publish data to a Redis channel.
    """
    redis_client.publish(channel, json.dumps(data))

def main():
    tickers = ["AAPL", "MSFT", "GOOGL"]  # Example tickers
    while True:
        for ticker in tickers:
            data = fetch_market_data(ticker)
            if data:
                publish_to_redis(REDIS_CHANNEL, data)
                print(f"Published data for {ticker} to Redis channel {REDIS_CHANNEL}")
        # Adjust sleep interval as needed
        time.sleep(60)

if __name__ == "__main__":
    main()
