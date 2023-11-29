import asyncio
import os
from typing import Any, AsyncGenerator
import anyio

import orjson
from tria_bot.clients.binance import AsyncClient
from tria_bot.models.proffit import Proffit
from tria_bot.schemas.message import ProffitMessage
from tria_bot.services.base import BaseSvc
from tria_bot.conf import settings


class ArbitrageSvc(BaseSvc):
    proffit_channel = settings.PUBSUB_PROFFIT_CHANNEL

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.__api_key = os.environ.get("BINANCE_API_KEY")
        self.__api_secret = os.environ.get("BINANCE_API_SECRET")
        self._binance = AsyncClient(
            api_key=self.__api_key,
            api_secret=self.__api_secret,
        )

    async def __aenter__(self) -> "ArbitrageSvc":
        await super().__aenter__()
        self._binance = await self._binance.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: Any | None = None,
        exc_val: Any | None = None,
        exc_tb: Any | None = None,
    ) -> None:
        await self._binance.__aexit__(exc_type, exc_val, exc_tb)
        return await super().__aexit__(exc_type, exc_val, exc_tb)

    async def ps_subscribe(self):
        async with self._redis_conn.pubsub(
            ignore_subscribe_messages=True
        ) as ps:
            await ps.subscribe(self.proffit_channel)
            self.logger.info(f"Subscribed to {self.proffit_channel}")
            async for msg in ps.listen():
                if msg != None:
                    self.logger.info("Top Volume Assets has changed")
                    self._is_running = False
                    await ps.unsubscribe()
                    break

    async def get_proffit(self) -> ProffitMessage:
        proffit = None
        async with self._redis_conn.pubsub(
            ignore_subscribe_messages=True
        ) as ps:
            await ps.subscribe(self.proffit_channel)
            self.logger.info(f"Subscribed to {self.proffit_channel}")

            async for msg in ps.listen():
                if msg != None:
                    proffit = ProffitMessage(
                        **orjson.loads(msg["data"].encode())
                    )
                    await ps.unsubscribe()
                    break
                # await asyncio.sleep(.001)

        return proffit

    async def arbitrate(self, proffit: Proffit) -> Any:
        # TODO: Arbitrate with inner proffit data
        self.logger.info(f"Arbitrating with {proffit}")
        return await asyncio.sleep(5.0)

    async def loop(self):
        proffit = await self.get_proffit()
        result = await self.arbitrate(proffit=Proffit(**proffit.data))
        # async for proffit in self.get_proffit():
        #     self.logger.info(f"Proffit detected! {proffit}")
        #     await asyncio.sleep(3.0)
        await asyncio.sleep(0.01)
        return await self.loop()

    @classmethod
    async def start(cls):
        async with cls() as svc:
            await svc.loop()


if __name__ == "__main__":
    anyio.run(ArbitrageSvc.start)
