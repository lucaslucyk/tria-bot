import asyncio
from tria_bot.services.tickers import TickerSvc

if __name__ == "__main__":
    asyncio.run(TickerSvc.subscribe())
