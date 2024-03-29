import asyncio
from typing import Any, Generator
from tria_bot.crud.composite import TopVolumeAssetsCRUD
from tria_bot.helpers.symbols import all_combos
from tria_bot.models.composite import TopVolumeAssets
from tria_bot.models.ticker import Ticker
from tria_bot.services.base import SocketBaseSvc, SocketError, SocketErrorDetail
from tria_bot.conf import settings


class TickerSvc(SocketBaseSvc[Ticker]):
    model = Ticker
    tva_model = TopVolumeAssets
    socket_handler_name = "ticker_socket"
    top_volume_channel = settings.PUBSUB_TOP_VOLUME_CHANNEL
    # socket_handler_name = "symbol_ticker_socket"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._symbols = None
        self._tva_crud = None
        self._tva = None

    async def _get_top_volume_assets(self):
        return await self._tva_crud.wait_for(self.tva_model.Meta.PK_VALUE)

    async def _get_symbols(self):
        return list(
            all_combos(
                alt_assets=self._tva.assets,
                stable_assets=(settings.USE_STABLE_ASSET,),
            )
        )

    async def __aenter__(self) -> "TickerSvc":
        await super().__aenter__()
        self._tva_crud = TopVolumeAssetsCRUD(conn=self._redis_conn)
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


    @classmethod
    async def start(cls) -> None:
        while True:
            async with cls() as ts:
                data = {
                    "STABLE": settings.USE_STABLE_ASSET,
                    "ALTCOINS": ts._tva.assets,
                }
                ts.logger.info(f"Starting service using {data}...")
                await asyncio.gather(ts.ws_subscribe(), ts.ps_subscribe())
                # await ts.subscribe()

