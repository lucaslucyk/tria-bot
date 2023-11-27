import anyio
from tria_bot.services.proffit import ProffitSvc


async def main():
    await ProffitSvc.start()


if __name__ == "__main__":
    anyio.run(main)
