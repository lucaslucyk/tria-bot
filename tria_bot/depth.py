import anyio
from tria_bot.services.depth import DepthSvc


async def main():
    SYMBOLS = (
        "BTCUSDT",
        "ETHUSDT",
        "BNBUSDT",
    )
    await DepthSvc.multi_subscribe(symbols=SYMBOLS)


if __name__ == "__main__":
    anyio.run(main)
