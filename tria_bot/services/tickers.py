import asyncio
from typing import Any, Generator

import orjson
from tria_bot.helpers.symbols import all_combos
from tria_bot.models.composite import TopVolumeAssets
from tria_bot.models.ticker import Ticker
from tria_bot.services.base import SocketBaseSvc, SocketError, SocketErrorDetail
from tria_bot.conf import settings


class TickerSvc(SocketBaseSvc[Ticker]):
    model = Ticker
    top_volume_model = TopVolumeAssets
    socket_handler_name = "ticker_socket"
    top_volume_channel = settings.PUBSUB_TOP_VOLUME_CHANNEL
    # socket_handler_name = "symbol_ticker_socket"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._symbols = None
        self._tva = None

    async def _get_top_volume_assets(self):
        return await self.top_volume_model.get(
            self.top_volume_model.Meta.PK_VALUE
        )

    async def _get_symbols(self):
        return list(
            all_combos(
                alt_assets=self._tva.assets,
                stable_assets=(settings.USE_STABLE_ASSET,),
            )
        )

    async def __aenter__(self) -> "TickerSvc":
        await super().__aenter__()
        self.top_volume_model.Meta.database = self._redis_conn
        self.top_volume_model._meta.database = self._redis_conn
        self._tva = await self._get_top_volume_assets()
        self._symbols = await self._get_symbols()
        return self

    async def ps_subscribe(self):
        async with self._redis_conn.pubsub(
            ignore_subscribe_messages=True
        ) as ps:
            await ps.subscribe(self.top_volume_channel)
            self.logger.info(f"Subscribed to {self.top_volume_channel}")
            async for msg in ps.listen():
                if msg != None:
                    self.logger.info("Top Volume Assets has changed")
                    self._is_running = False
                    await ps.unsubscribe()
                    break

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
    async def subscribe(cls) -> Any:
        while True:
            async with cls() as ts:
                data = {
                    "STABLE": settings.USE_STABLE_ASSET,
                    "ALTCOINS": ts._tva.assets,
                }
                ts.logger.info(f"Starting service using {data}...")
                await asyncio.gather(ts.ws_subscribe(), ts.ps_subscribe())
                # await ts.subscribe()

    # @classmethod
    # async def multi_subscribe(cls, symbols: Iterable[str]) -> Any:
    #     tasks = [cls._subscribe(s) for s in symbols]
    #     await asyncio.gather(*tasks, return_exceptions=True)
