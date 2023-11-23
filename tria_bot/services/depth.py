from time import time
from typing import Any, Generator
import anyio
from tria_bot.models.depth import Depth
from tria_bot.services.base import SocketBaseSvc, SocketError, SocketErrorDetail


class DepthSvc(SocketBaseSvc[Depth]):
    model = Depth
    socket_handler_name = "depth_socket"

    def __init__(self, *args, symbol: str, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.symbol = symbol

    async def __aenter__(self) -> "DepthSvc":
        return await super().__aenter__()

    def _model_or_raise(self, data: Any) -> Generator[Depth, Any, None]:
        try:
            yield self.model(
                **data,
                symbol=self.symbol,
                event_time=int(time()),
            )
        except:
            raise SocketError(SocketErrorDetail(**data))

    async def subscribe(self) -> None:
        return await super().subscribe(
            symbol=self.symbol,
            depth=self._socket_manager.WEBSOCKET_DEPTH_5,
            interval=100,
        )


async def main():
    async with DepthSvc(symbol="BTCUSDT") as ts:
        # ts._socket_manager.depth_socket()
        await ts.subscribe()


if __name__ == "__main__":
    anyio.run(main)
