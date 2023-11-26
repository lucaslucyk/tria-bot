import anyio
from tria_bot.services.tickers import TickerSvc


async def main():
    await TickerSvc.start()


if __name__ == "__main__":
    anyio.run(main)
