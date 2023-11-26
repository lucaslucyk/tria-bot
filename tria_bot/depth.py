import asyncio
from tria_bot.services.depth import DepthSvc


async def main(splitter: str) -> None:
    await DepthSvc.start(splitter=splitter)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Args to run depths")
    parser.add_argument(
        "-s",
        "--splitter",
        type=str,
        default="1/1",
        help="Service index / Total services",
    )

    asyncio.run(main(**vars(parser.parse_args())))
