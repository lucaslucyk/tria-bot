# type: ignore

import pytest
import pytest_asyncio

# We need to run this check as sync code (during tests) even in async mode
# because we call it in the top-level module scope.
from redis_om import has_redis_json
from tria_bot.models.composite import (
    Symbol,
    TopVolumeAssets,
    ValidSymbols,
)
from tria_bot.tests.conftest import pytest_mark_asyncio


if not has_redis_json():
    pytestmark = pytest.mark.skip

@pytest.fixture()
def symbol():
    yield Symbol(
        symbol="FAKESYMBOL",
        base_asset="FAKE",
        quote_asset="SYMBOL",
        is_spot_trading_allowed=True,
        min_price=0.0007,
        max_price=2.05467,
        tick_size=0.00001,
        min_qty=0.005,
        max_qty=5.0,
        step_size=0.0001,
        order_types=["SPOT", "LIMIT"],
        permissions=["TRADE", "..."],
        status="TRADING",
    )


@pytest.fixture()
def top_volume_assets():
    yield TopVolumeAssets(assets=["FAKE1", "FAKE2", "FAKE3"])


@pytest.fixture()
def valid_symbols():
    yield ValidSymbols(symbols=["FAKE1", "FAKE2", "FAKE3"])


@pytest_mark_asyncio
async def test_save_symbol(symbol, crud):
    r = await crud.symbols.save(symbol)
    assert r == symbol


@pytest_mark_asyncio
async def test_save_tva(top_volume_assets, crud):
    r = await crud.top_volume_assets.save(top_volume_assets)
    assert r == top_volume_assets


@pytest_mark_asyncio
async def test_save_vs(valid_symbols, crud):
    r = await crud.valid_symbols.save(valid_symbols)
    assert r == valid_symbols
