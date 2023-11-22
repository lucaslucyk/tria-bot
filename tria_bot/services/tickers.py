import anyio
from tria_bot.models.ticker import Ticker
from tria_bot.services.base import BaseSvc


class TickerSvc(BaseSvc[Ticker]):
    model = Ticker
    socket_handler_name = "ticker_socket"

    async def __aenter__(self) -> "TickerSvc":
        return await super().__aenter__()


async def main():
    async with TickerSvc() as ts:
        await ts.subscribe()


if __name__ == "__main__":
    anyio.run(main)
