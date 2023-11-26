import asyncio
from time import time_ns
from typing import Any, Generator, Iterable, List
from tria_bot.crud.composite import ValidSymbolsCRUD
from tria_bot.models.composite import ValidSymbols
from tria_bot.models.depth import Depth
from tria_bot.services.base import SocketBaseSvc
from tria_bot.conf import settings


class DepthSvc(SocketBaseSvc[Depth]):
    model = Depth
    socket_handler_name = "depth_socket"
    top_volume_channel = settings.PUBSUB_TOP_VOLUME_CHANNEL
    # valid_sybols_model = ValidSymbols

    def __init__(self, *args, symbol: str, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.symbol = symbol

    async def __aenter__(self) -> "DepthSvc":
        return await super().__aenter__()

    def _model_or_raise(self, data: Any) -> Generator[Depth, Any, None]:
        return super()._model_or_raise(
            data={
                **data,
                "symbol": self.symbol,
                "event_time": int(time_ns() / 1000000),
            }
        )

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

    async def ws_subscribe(self) -> None:
        # self._socket_manager.depth_socket()
        return await super().ws_subscribe(
            symbol=self.symbol,
            depth=self._socket_manager.WEBSOCKET_DEPTH_5,
            interval=100,
        )

    @classmethod
    async def subscribe(cls, symbol: str) -> Any:
        while True:
            async with cls(symbol=symbol) as ts:
                await asyncio.gather(ts.ws_subscribe(), ts.ps_subscribe())

    @classmethod
    async def _get_valid_symbols(cls) -> ValidSymbols:
        async with ValidSymbolsCRUD() as crud:
            return await crud.wait_for(ValidSymbols.Meta.PK_VALUE)

    @classmethod
    async def _get_symbols(cls, splitter: str) -> List[str]:
        valid_symbols = await cls._get_valid_symbols()
        page, pages = splitter.strip().split("/")
        page, pages = int(page), int(pages)
        total_symbols = len(valid_symbols.symbols)
        qty = int(total_symbols / pages)
        start = (page - 1) * qty
        end = total_symbols if page == pages else page * qty
        return valid_symbols.symbols[start:end]

    @classmethod
    async def multi_subscribe(cls, symbols: Iterable[str]) -> None:
        tasks = [cls.subscribe(s) for s in symbols]
        await asyncio.gather(*tasks, return_exceptions=True)

    @classmethod
    async def start(cls, splitter: str):
        symbols = await cls._get_symbols(splitter)
        if not symbols:
            return

        await cls.multi_subscribe(symbols=symbols)
