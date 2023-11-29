import anyio
from tria_bot.services.arbitrage import ArbitrageSvc


async def main():
    await ArbitrageSvc.start()


if __name__ == "__main__":
    anyio.run(main)
