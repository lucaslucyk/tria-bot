from tria_bot.helpers.symbols import (
    all_combos,
    alt_combos,
    stable_alt_combos,
    strong_alt_combos,
    strong_stable_combos,
)


STABLE_ASSETS = ("USDT", "DAI")
STRONG_ASSETS = ("BTC", "ETH")
ALT_ASSETS = ("SOL", "XRP")


def test_alt_combos():
    alt = ALT_ASSETS[0]
    combos = alt_combos(
        alt_asset=alt,
        strong_assets=STRONG_ASSETS,
        stable_assets=STABLE_ASSETS,
    )

    expected = (
        f"{alt}USDT",
        f"{alt}DAI",
        f"{alt}BTC",
        f"{alt}ETH",
    )

    assert set(combos) == set(expected)


def test_strong_alt_combos():
    stg = STRONG_ASSETS[0]
    combos = strong_alt_combos(strong_asset=stg, alt_assets=ALT_ASSETS)
    expected = (f"{ALT_ASSETS[0]}{stg}", f"{ALT_ASSETS[1]}{stg}")
    assert set(combos) == set(expected)


def test_stable_alt_combos():
    stb = STABLE_ASSETS[0]
    combos = stable_alt_combos(stable_asset=stb, alt_assets=ALT_ASSETS)
    expected = (f"{ALT_ASSETS[0]}{stb}", f"{ALT_ASSETS[1]}{stb}")
    assert set(combos) == set(expected)


def test_strong_stable_combos():
    combos = strong_stable_combos(
        strong_assets=STRONG_ASSETS,
        stable_assets=STABLE_ASSETS,
    )
    expected = (
        f"{STRONG_ASSETS[0]}{STABLE_ASSETS[0]}",
        f"{STRONG_ASSETS[0]}{STABLE_ASSETS[1]}",
        f"{STRONG_ASSETS[1]}{STABLE_ASSETS[0]}",
        f"{STRONG_ASSETS[1]}{STABLE_ASSETS[1]}",
    )
    assert set(combos) == set(expected)


def test_all_combos():
    combos = all_combos(
        alt_assets=ALT_ASSETS,
        strong_assets=STRONG_ASSETS,
        stable_assets=STABLE_ASSETS,
    )

    expected = (
        f"{ALT_ASSETS[0]}{STRONG_ASSETS[0]}",
        f"{ALT_ASSETS[0]}{STRONG_ASSETS[1]}",
        f"{ALT_ASSETS[1]}{STRONG_ASSETS[0]}",
        f"{ALT_ASSETS[1]}{STRONG_ASSETS[1]}",

        f"{ALT_ASSETS[0]}{STABLE_ASSETS[0]}",
        f"{ALT_ASSETS[0]}{STABLE_ASSETS[1]}",
        f"{ALT_ASSETS[1]}{STABLE_ASSETS[0]}",
        f"{ALT_ASSETS[1]}{STABLE_ASSETS[1]}",

        f"{STRONG_ASSETS[0]}{STABLE_ASSETS[0]}",
        f"{STRONG_ASSETS[0]}{STABLE_ASSETS[1]}",
        f"{STRONG_ASSETS[1]}{STABLE_ASSETS[0]}",
        f"{STRONG_ASSETS[1]}{STABLE_ASSETS[1]}",
    )
    assert set(combos) == set(expected)