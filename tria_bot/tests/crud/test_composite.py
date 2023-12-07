# type: ignore

import asyncio
import os
import pytest
import pytest_asyncio

# We need to run this check as sync code (during tests) even in async mode
# because we call it in the top-level module scope.
from redis_om import has_redis_json
from aredis_om import NotFoundError
from tria_bot.crud.composite import SymbolsCRUD
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
    # TODO: change this to yield crud.symbols.model(...)
    # to ensure model._meta.database connection
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
def symbols():
    # TODO: change this to yield crud.symbols.model(...)
    # to ensure model._meta.database connection
    s1 = Symbol(
        symbol="FAKESYMBOL1",
        base_asset="FAKE",
        quote_asset="SYMBOL1",
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

    s2 = Symbol(
        symbol="FAKESYMBOL2",
        base_asset="FAKE",
        quote_asset="SYMBOL2",
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
    yield s1, s2


@pytest.fixture()
def top_volume_assets():
    # TODO: change this to yield crud.top_volume_assets.model(...)
    # to ensure model._meta.database connection
    yield TopVolumeAssets(
        pk=TopVolumeAssets.Meta.PK_VALUE, assets=["FAKE1", "FAKE2", "FAKE3"]
    )


@pytest.fixture()
def valid_symbols():
    # TODO: change this to yield crud.valid_symbols.model(...)
    # to ensure model._meta.database connection
    yield ValidSymbols(
        pk=ValidSymbols.Meta.PK_VALUE, symbols=["FAKE1", "FAKE2", "FAKE3"]
    )


@pytest_mark_asyncio
async def test_save(crud, symbol, top_volume_assets, valid_symbols):
    s = await crud.symbols.save(symbol)
    assert s == symbol

    tva = await crud.top_volume_assets.save(top_volume_assets)
    assert tva == top_volume_assets

    vs = await crud.valid_symbols.save(valid_symbols)
    assert vs == valid_symbols


@pytest_mark_asyncio
async def test_get(crud, symbol, top_volume_assets, valid_symbols):
    s = await crud.symbols.get(symbol.symbol)
    assert s == symbol

    tva = await crud.top_volume_assets.get(top_volume_assets.pk)
    assert tva == top_volume_assets

    vs = await crud.valid_symbols.get(valid_symbols.pk)
    assert vs == valid_symbols


@pytest_mark_asyncio
async def test_not_found_symbol(crud):
    with pytest.raises(NotFoundError) as err:
        await crud.symbols.get("NOTFOUNDSYMBOL")

    with pytest.raises(NotFoundError) as err:
        await crud.top_volume_assets.get("NOTFOUNDTVA")

    with pytest.raises(NotFoundError) as err:
        await crud.valid_symbols.get("NOTFOUNDVS")


@pytest_mark_asyncio
async def test_wait_for(crud, symbol, top_volume_assets, valid_symbols):
    s = await crud.symbols.wait_for(symbol.symbol)
    assert s == symbol

    tva = await crud.top_volume_assets.wait_for(top_volume_assets.pk)
    assert tva == top_volume_assets

    vs = await crud.valid_symbols.wait_for(valid_symbols.pk)
    assert vs == valid_symbols


@pytest_mark_asyncio
async def test_wait_for_not_found(crud):
    S = "DELETESYMBOL"

    async def new_symbol() -> Symbol:
        await asyncio.sleep(1.0)
        s = crud.symbols.model(
            symbol=S,
            base_asset="DELETE",
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
        return await crud.symbols.save(s)

    tasks = [crud.symbols.wait_for(S), new_symbol()]
    results = await asyncio.gather(*tasks)
    assert results[0].symbol == S

    # ensure delete to prevent next steps
    await crud.symbols.model.delete(S)


@pytest_mark_asyncio
async def test_all_pks(crud, symbol, top_volume_assets, valid_symbols):
    symbol_pks = [pk async for pk in crud.symbols.all_pks()]
    assert [symbol.pk] == symbol_pks

    tva_pks = [pk async for pk in crud.top_volume_assets.all_pks()]
    assert [top_volume_assets.pk] == tva_pks

    vs_pks = [pk async for pk in crud.valid_symbols.all_pks()]
    assert [valid_symbols.pk] == vs_pks


@pytest_mark_asyncio
async def test_add(crud, symbols):
    # symbol_models = [s for s in symbols]
    r = await crud.symbols.add(models=symbols)
    for s in symbols:
        assert s in r


@pytest_mark_asyncio
async def test_get_all(crud, symbols, symbol, top_volume_assets, valid_symbols):
    sr = [s async for s in crud.symbols.get_all()]
    response_symbols = set(s.symbol for s in sr)
    inner_symbols = set(s.symbol for s in (symbol, *symbols))
    assert inner_symbols == response_symbols

    tvar = [tva async for tva in crud.top_volume_assets.get_all()]
    assert tvar == [top_volume_assets]

    vsr = [vs async for vs in crud.valid_symbols.get_all()]
    assert vsr == [valid_symbols]


@pytest_mark_asyncio
async def test_no_redis_conn(symbol):
    async with SymbolsCRUD() as sc:
        s = await sc.get(symbol.symbol)
        assert s == symbol
