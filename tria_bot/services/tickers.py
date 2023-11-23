import asyncio
from typing import Any, Generator, Sequence
from tria_bot.models.ticker import Ticker
from tria_bot.services.base import SocketBaseSvc, SocketError, SocketErrorDetail


class TickerSvc(SocketBaseSvc[Ticker]):
    model = Ticker
    socket_handler_name = "ticker_socket"
    # socket_handler_name = "symbol_ticker_socket"

    def __init__(self, *args, symbols: Sequence[str], **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.symbols = symbols

    async def __aenter__(self) -> "TickerSvc":
        return await super().__aenter__()

    def _model_or_raise(self, data: Any) -> Generator[Ticker, Any, None]:
        if isinstance(data, list):
            for obj in data:
                if obj.get("s", None) in self.symbols:
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
    async def _subscribe(cls, symbols: Sequence[str]) -> Any:
        async with cls(symbols=symbols) as ts:
            await ts.subscribe()

    # @classmethod
    # async def multi_subscribe(cls, symbols: Iterable[str]) -> Any:
    #     tasks = [cls._subscribe(s) for s in symbols]
    #     await asyncio.gather(*tasks, return_exceptions=True)
