# type: ignore

import pytest
import pytest_asyncio
from typing import Generator, Any

# We need to run this check as sync code (during tests) even in async mode
# because we call it in the top-level module scope.
from redis_om import has_redis_json
from tria_bot.helpers.binance import Binance as BinanceHelper
from tria_bot.models.composite import Symbol


if not has_redis_json():
    pytestmark = pytest.mark.skip


@pytest.fixture(scope="session")
def symbols(crud) -> Generator[tuple[Symbol, Symbol], Any, None]:
    Model = crud.symbols.model
    s0 = Model(
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
    s1 = Model(
        symbol="FAKESYMBOL1",
        base_asset="FAKE",
        quote_asset="SYMBOL1",
        is_spot_trading_allowed=True,
        min_price=0.0007,
        max_price=2.05467,
        tick_size=0.000001,
        min_qty=0.005,
        max_qty=5.0,
        step_size=0.0001,
        order_types=["SPOT", "LIMIT"],
        permissions=["TRADE", "..."],
        status="TRADING",
    )

    s2 = Model(
        symbol="FAKESYMBOL2",
        base_asset="FAKE",
        quote_asset="SYMBOL2",
        is_spot_trading_allowed=True,
        min_price=0.0007,
        max_price=2.05467,
        tick_size=0.00000001,
        min_qty=0.005,
        max_qty=5.0,
        step_size=0.0001,
        order_types=["SPOT", "LIMIT"],
        permissions=["TRADE", "..."],
        status="TRADING",
    )
    s3 = Model(
        symbol="FAKESYMBOL3",
        base_asset="FAKE",
        quote_asset="SYMBOL3",
        is_spot_trading_allowed=True,
        min_price=0.0007,
        max_price=2.05467,
        tick_size=0.0,
        min_qty=0.005,
        max_qty=5.0,
        step_size=0.0001,
        order_types=["SPOT", "LIMIT"],
        permissions=["TRADE", "..."],
        status="TRADING",
    )
    yield s0, s1, s2, s3


def test_map_symbols(symbols):
    helper = BinanceHelper(symbols=symbols)
    assert helper._symbols_info.get("FAKESYMBOL") == symbols[0]


def test_symbol_size(symbols):
    helper = BinanceHelper(symbols=symbols)

    value = 545.168734897
    step_size = helper.get_step_size(symbol="FAKESYMBOL")
    assert step_size == 0.0001

    step_sized = helper.apply_step_size(symbol="FAKESYMBOL", value=value)
    assert step_sized == 545.1687

    tick_size = helper.get_tick_size(symbol="FAKESYMBOL1")
    assert tick_size == 0.000001

    tick_sized = helper.apply_tick_size(symbol="FAKESYMBOL1", value=value)
    assert tick_sized == 545.168734


def test_ffp(symbols):
    helper = BinanceHelper(symbols=symbols)

    value = 0.00000475
    tick_sized = helper.apply_tick_size(symbol="FAKESYMBOL2", value=value)
    ffpd = helper._ffp(tick_sized)

    assert ffpd == "0.00000475"


def test_size_error(symbols):
    helper = BinanceHelper(symbols=symbols)

    with pytest.raises(KeyError) as err:
        size = helper._get_size(symbol="SYMBOLNOTFOUND", kind="step")

    with pytest.raises(ValueError) as err:
        size = helper._get_size(symbol="FAKESYMBOL3", kind="tick")