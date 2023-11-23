from typing import Iterable


STABLE_ASSETS = (
    "USDT",
    "DAI",
    "BUSD",
    "TUSD",
    "USDC",
    "UST",
    "DGX",
    "PAX",
    "USDN",
    "TRIBE",
)

STRONG_ASSETS = (
    "BTC",
    "ETH",
    "BNB",
)


def alt_combos(
    alt_asset: str,
    strong_assets: Iterable[str] = STRONG_ASSETS,
    stable_assets: Iterable[str] = STABLE_ASSETS,
):
    for stable in stable_assets:
        yield f"{alt_asset}{stable}"
    for strong in strong_assets:
        yield f"{alt_asset}{strong}"


def strong_alt_combos(
    strong_asset: str,
    alt_assets: Iterable[str],
):
    for alt in alt_assets:
        yield f"{alt}{strong_asset}"


def stable_alt_combos(
    stable_asset: str,
    alt_assets: Iterable[str],
):
    for alt in alt_assets:
        yield f"{alt}{stable_asset}"


def strong_stable_combos(
    strong_assets: Iterable[str] = STRONG_ASSETS,
    stable_assets: Iterable[str] = STABLE_ASSETS,
):
    for stable in stable_assets:
        for strong in strong_assets:
            yield f"{strong}{stable}"


def all_combos(
    alt_assets: Iterable[str],
    strong_assets: Iterable[str] = STRONG_ASSETS,
    stable_assets: Iterable[str] = STABLE_ASSETS,
):  
    for strong in strong_assets:
        yield from strong_alt_combos(strong_asset=strong, alt_assets=alt_assets)
    
    for stable in stable_assets:
        yield from stable_alt_combos(stable_asset=stable, alt_assets=alt_assets)
    
    yield from strong_stable_combos(strong_assets=strong_assets, stable_assets=stable_assets)
