import anyio
from tria_bot.services.gap import GapCalculatorSvc


async def main():
    async with GapCalculatorSvc() as svc:
        await svc.start()


if __name__ == "__main__":
    anyio.run(main)
