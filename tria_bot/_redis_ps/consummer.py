# from asyncio import sleep, run
# from asyncio.exceptions import TimeoutError, CancelledError
from datetime import datetime
from typing import Any, Dict
import anyio
import os
from aredis_om import get_redis_connection
import orjson

async def handler(message: Dict[str, Any]) -> None:
    try:
        print("time:", datetime.now().isoformat())
        print(orjson.loads(message["data"]))
    except orjson.JSONDecodeError:
        print(message)


async def publish():
    """Read events from pub-sub channel."""
    pubsub_channel = "dev"
    redis_url = os.environ.get("REDIS_PUB_SUB_URL", "redis://localhost:6379")
    redis = get_redis_connection(url=redis_url)

    async with redis.pubsub(ignore_subscribe_messages=True) as ps:
        await ps.subscribe(pubsub_channel)
        async for msg in ps.listen():
            # {'type': 'message', 'pattern': None, 'channel': 'dev', 'data': '...'}
            if msg["type"] != "message":
                continue
            await handler(msg)
        
        # await ps.subscribe(**{pubsub_channel: handler})
        # thread = None
        # try:
        #     thread = await ps.run()
        # except KeyboardInterrupt:
        #     # when it's time to shut it down...
        #     if thread != None:
        #         thread.stop()

if __name__ == "__main__":
    anyio.run(publish)