import anyio
from tria_bot.services.tickers import TickerSvc


async def main():
    await TickerSvc.subscribe()


if __name__ == "__main__":
    anyio.run(main)
