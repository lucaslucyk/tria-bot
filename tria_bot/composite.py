import anyio
from tria_bot.services.composite import CompositeSvc


async def main():
    await CompositeSvc._refresh(interval=3.0)


if __name__ == "__main__":
    anyio.run(main)
