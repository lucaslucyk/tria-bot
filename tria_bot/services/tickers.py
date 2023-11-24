import asyncio
import anyio
from aredis_om.connections import redis
from threading import Thread
from typing import Any, Generator, Sequence

import orjson
from tria_bot.helpers.symbols import all_combos
from tria_bot.models.composite import TopVolumeAssets
from tria_bot.models.ticker import Ticker
from tria_bot.services.base import SocketBaseSvc, SocketError, SocketErrorDetail
from tria_bot.conf import settings


class Listener(Thread):
    def __init__(
        self, *args, redis_conn: redis.Redis, svc: "TickerSvc", **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self._redis_conn = redis_conn
        self._svc = svc
        self._channel = settings.PUBSUB_TOP_VOLUME_CHANNEL

    async def main(self):
        async with self._redis_conn.pubsub(
            ignore_subscribe_messages=True
        ) as ps:
            await ps.subscribe(self._channel)
            self._svc.logger.info(f"Subscribed to {self._channel}")
            async for msg in ps.listen():
                # {'type': 'message', 'pattern': None, 'channel': 'dev', 'data': '...'}
                # if msg["type"] != "message":
                #     continue
                if msg != None:
                    data = orjson.loads(msg["data"])
                    self._svc.logger.info(data)
                    self._svc.logger.info("Stopping svc...")
                    self._svc._is_running = False
                    await ps.unsubscribe()
                    break

    def run(self):
        asyncio.run(self.main())
    # def run(self) -> None:
    #     task = asyncio.create_task(self.main())
    #     try:
    #         asyncio.shield(task)
    #     except asyncio.CancelledError:
    #         print("Main task cancelled")


class TickerSvc(SocketBaseSvc[Ticker]):
    model = Ticker
    top_volume_model = TopVolumeAssets
    socket_handler_name = "ticker_socket"
    # socket_handler_name = "symbol_ticker_socket"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._symbols = None
        self._listener = None

    # def __init__(self, *args, symbols: Sequence[str], **kwargs) -> None:
    #     super().__init__(*args, **kwargs)
    #     self.symbols = symbols
    #     self._listener = None


    async def _get_symbols(self):
        tva = await self.top_volume_model.get(
            self.top_volume_model.Meta.PK_VALUE
        )
        return list(
            all_combos(
                alt_assets=tva.assets,
                stable_assets=(settings.USE_STABLE_ASSET,),
            )
        )

    async def __aenter__(self) -> "TickerSvc":
        await super().__aenter__()
        self.top_volume_model.Meta.database = self._redis_conn
        self.top_volume_model._meta.database = self._redis_conn
        self._symbols = await self._get_symbols()
        self._listener = Listener(redis_conn=self._redis_conn, svc=self)
        self._listener.start()
        return self

    def _model_or_raise(self, data: Any) -> Generator[Ticker, Any, None]:
        if isinstance(data, list):
            for obj in data:
                if obj.get("s", None) in self._symbols:
                    yield self.model(**obj)

        elif isinstance(data, dict):
            try:
                yield self.model(**data)
            except:
                raise SocketError(SocketErrorDetail(**data))
        else:
            raise ValueError("Not supported data")

    # async def subscribe(self) -> Any:
    #     # self._socket_manager.depth_socket()
    #     return await super().subscribe(symbol=self.symbol)

    @classmethod
    async def _subscribe(cls) -> Any:
        while True:
            async with cls() as ts:
                await ts.subscribe()

    # @classmethod
    # async def multi_subscribe(cls, symbols: Iterable[str]) -> Any:
    #     tasks = [cls._subscribe(s) for s in symbols]
    #     await asyncio.gather(*tasks, return_exceptions=True)
