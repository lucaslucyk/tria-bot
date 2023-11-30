import asyncio
import anyio


async def main(strict: bool):
    await asyncio.sleep(1)
    print("strict", strict)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Args to run proffits")
    parser.add_argument(
        "--strict",
        type=bool,
        default=False,
        action=argparse.BooleanOptionalAction,
    )
    asyncio.run(main(**vars(parser.parse_args())))
