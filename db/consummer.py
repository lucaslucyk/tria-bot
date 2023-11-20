import anyio
from models import Customer


async def main():
    async for c in await Customer.all_pks():
        d = await Customer.get(c)
        print(d.dict())

if __name__ == "__main__":
    anyio.run(main)
