import anyio
from tria_bot.models.ticker import Ticker


async def main():
    t = Ticker(symbol='BNBBTC', price_change='0.0015', price_change_percent='250.00', event_time=123456789)
    r = await t.save()
    print(r)


if __name__ == "__main__":
    anyio.run(main)