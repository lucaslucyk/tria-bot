from asyncio.exceptions import TimeoutError, CancelledError
from datetime import datetime
import anyio
import os
from aredis_om import get_redis_connection


async def publish():
    """Read events from pub-sub channel."""
    pubsub_channel = "dev"
    message = "testing message v2"
    redis_url = os.environ.get("REDIS_PUB_SUB_URL", "redis://localhost:6379")
    redis = get_redis_connection()
    try:
        for _ in range(5):
            r = await redis.publish(pubsub_channel, message)
            print("time:", datetime.now().isoformat())
    except (ConnectionError, TimeoutError, CancelledError) as err:
        print(err)


if __name__ == "__main__":
    anyio.run(publish)