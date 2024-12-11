from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

# Fetch and print environment variables
print("Polygon API Key:", os.getenv("POLYGON_API_KEY"))
print("Redis Host:", os.getenv("REDIS_HOST"))
print("Redis Port:", os.getenv("REDIS_PORT"))
print("Redis Channel:", os.getenv("REDIS_CHANNEL"))
print("S3 Bucket:", os.getenv("S3_BUCKET"))
print("S3 Endpoint:", os.getenv("S3_ENDPOINT"))

