import anyio
from tria_bot.models.ticker import Ticker
from aredis_om import Migrator, get_redis_connection


async def main():
    await Migrator().run()

    async for t in await Ticker.all_pks():
        print(await Ticker.get(t))

if __name__ == "__main__":
    anyio.run(main)
