import redis
import os

def get_redis_client():
    try:
        return redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            decode_responses=True
        )
    except Exception:
        return None

def save_high_priority(complaint_id, data):
    try:
        client = get_redis_client()
        if client:
            client.hset(f"complaint:{complaint_id}", mapping=data)
    except Exception:
        # Redis is optional — fail silently
        pass
