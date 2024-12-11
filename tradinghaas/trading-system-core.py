import os
import redis
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path="./.env")

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_CHANNEL = os.getenv("REDIS_CHANNEL", "market-data")

# Connect to Redis
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)

def process_market_data(data):
    """
    Process incoming market data and implement trading logic.
    """
    print(f"Processing data: {data}")
    # Placeholder for actual trading logic

def main():
    pubsub = redis_client.pubsub()
    pubsub.subscribe(REDIS_CHANNEL)

    print(f"Subscribed to Redis channel {REDIS_CHANNEL}. Waiting for market data...")

    for message in pubsub.listen():
        if message and message["type"] == "message":
            data = json.loads(message["data"])
            process_market_data(data)

if __name__ == "__main__":
    main()
