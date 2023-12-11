# type: ignore

import asyncio
import pytest
import pytest_asyncio
from typing import Generator, Any

# We need to run this check as sync code (during tests) even in async mode
# because we call it in the top-level module scope.
from redis_om import has_redis_json
from aredis_om import NotFoundError
from tria_bot.models.depth import Depth
from tria_bot.tests.conftest import pytest_mark_asyncio


if not has_redis_json():
    pytestmark = pytest.mark.skip


@pytest.fixture(scope="session")
def depth(crud) -> Generator[Depth, Any, None]:
    yield crud.depths.model(
        symbol="FAKESYMBOL",
        bids=[("0.468746", "685465.4"), ("0.6878", "6885.1")],
        asks=[("0.478166", "6548.4"), ("0.67488", "6878.2")],
        event_time=123456789,
    )


@pytest_mark_asyncio
async def test_save(crud, depth):
    d = await crud.depths.save(depth)
    assert d == depth


@pytest_mark_asyncio
async def test_get(crud, depth):
    s = await crud.depths.get(depth.symbol)
    assert s == depth


@pytest_mark_asyncio
async def test_not_found(crud):
    with pytest.raises(NotFoundError) as err:
        await crud.depths.get("NOTFOUNDSYMBOL")


@pytest_mark_asyncio
async def test_wait_for(crud):
    S = "DELETESYMBOL"

    async def new_depth() -> Depth:
        await asyncio.sleep(1.0)
        d = crud.depths.model(
            symbol=S,
            bids=[("0.468746", "685465.4"), ("0.6878", "6885.1")],
            asks=[("0.478166", "6548.4"), ("0.67488", "6878.2")],
            event_time=684685,
        )
        return await crud.depths.save(d)

    tasks = [crud.depths.wait_for(S), new_depth()]
    results = await asyncio.gather(*tasks)
    assert results[0].symbol == S

    # ensure delete to prevent next steps
    await crud.depths.model.delete(S)


@pytest_mark_asyncio
async def test_all_pks(crud, depth):
    depth_pks = [pk async for pk in crud.depths.all_pks()]
    assert [depth.pk] == depth_pks


@pytest_mark_asyncio
async def test_get_all(crud, depth):
    ds = [d async for d in crud.depths.get_all()]
    assert ds == [depth]
