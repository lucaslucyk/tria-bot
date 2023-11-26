import anyio
from tria_bot.services.gap import GapCalculatorSvc


async def main():
    await GapCalculatorSvc.start()


if __name__ == "__main__":
    anyio.run(main)
