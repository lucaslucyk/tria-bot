import asyncio
from typing import Literal, Optional
from aredis_om import NotFoundError
from tria_bot.helpers.symbols import (
    stable_alt_combos,
    strong_alt_combos,
    strong_stable_combos,
)
from tria_bot.models.composite import TopVolumeAssets as TVA
from tria_bot.services.depth import DepthSvc
from tria_bot.conf import settings


async def get_tva(attempt: int = 0):
    try:
        tva = await TVA.get(TVA.Meta.PK_VALUE)
        return tva.assets
    except NotFoundError:
        await asyncio.sleep(1.0)
        return await get_tva(attempt+1)


async def main(kind: str, strong: Optional[str] = None):
    kinds = {
        "strong_stable": strong_stable_combos(
            stable_assets=(settings.USE_STABLE_ASSET,)
        ),
        "alt_stable": stable_alt_combos(
            stable_asset=settings.USE_STABLE_ASSET,
            alt_assets=await get_tva(),
        ),
        "alt_strong": strong_alt_combos(
            strong_asset=strong,
            alt_assets=await get_tva(),
        ),
    }
    symbols = list(kinds.get(kind, []))
    if not symbols: return
    await DepthSvc.multi_subscribe(symbols=symbols)


if __name__ == "__main__":
    import argparse


    parser = argparse.ArgumentParser(description='Args to run depths')
    parser.add_argument(
        '-k',
        '--kind',
        type=str,
        default="strong_stable",
        help='Depth kind'
    )
    parser.add_argument(
        '-s',
        '--strong',
        type=str,
        default=None,
        help='Strong asset to use in alt_strong kind'
    )

    asyncio.run(main(**vars(parser.parse_args())))
