import asyncio
from time import time_ns
from typing import Any, Generator, Iterable
from tria_bot.models.depth import Depth
from tria_bot.services.base import SocketBaseSvc


class DepthSvc(SocketBaseSvc[Depth]):
    model = Depth
    socket_handler_name = "depth_socket"

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

    async def ws_subscribe(self) -> None:
        # self._socket_manager.depth_socket()
        return await super().ws_subscribe(
            symbol=self.symbol,
            depth=self._socket_manager.WEBSOCKET_DEPTH_5,
            interval=100,
        )

    @classmethod
    async def subscribe(cls, symbol: str) -> Any:
        async with cls(symbol=symbol) as ts:
            await ts.ws_subscribe()
    
    @classmethod
    async def multi_subscribe(cls, symbols: Iterable[str]) -> Any:
        tasks = [cls.subscribe(s) for s in symbols]
        await asyncio.gather(*tasks, return_exceptions=True)
