import asyncio
from tria_bot.services.proffit import ProffitSvc


async def main(strict: bool):
    await ProffitSvc.start(strict=strict)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Args to run proffits")
    parser.add_argument(
        "--strict",
        type=bool,
        default=False,
        action=argparse.BooleanOptionalAction,
        help="Use gaps to calc proffits",
    )
    asyncio.run(main(**vars(parser.parse_args())))
