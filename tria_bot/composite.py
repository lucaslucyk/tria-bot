import anyio
from tria_bot.services.composite import CompositeSvc


async def main():
    await CompositeSvc.start()


if __name__ == "__main__":
    anyio.run(main)
