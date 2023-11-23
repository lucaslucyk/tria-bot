import asyncio
from tria_bot.services.composite import CompositeSvc


if __name__ == "__main__":
    asyncio.run(CompositeSvc._refresh(interval=3.0))
