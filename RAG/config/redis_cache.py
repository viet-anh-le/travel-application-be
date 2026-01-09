# app/config/redis_cache.py
import redis.asyncio as redis

# Giả sử bạn thêm REDIS_HOST và REDIS_PORT vào file .env hoặc settings
REDIS_HOST = "localhost"
REDIS_PORT = "6379"
print(f"\n---------------------Connecting to Redis at {REDIS_HOST}:{REDIS_PORT}---------------------\n")

try:
    # Tạo một connection pool
    redis_pool = redis.ConnectionPool(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=0,
        decode_responses=True
    )
except Exception as e:
    print(f"Failed to create Redis pool: {e}")
    redis_pool = None
    
redis_client = redis.Redis(connection_pool=redis_pool)

async def get_redis_instance():
    """Dependency function to get a Redis connection from the pool."""
    if redis_pool is None:
        raise RuntimeError("Redis connection pool is not initialized.")
    try:
        yield redis_client
    except redis.exceptions.ConnectionError as e:
        raise RuntimeError(f"Failed to connect to Redis: {e}")