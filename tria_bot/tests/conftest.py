import asyncio
from collections import namedtuple
import pytest

from aredis_om import get_redis_connection, Migrator
import pytest_asyncio

from tria_bot.crud.composite import (
    SymbolsCRUD,
    TopVolumeAssetsCRUD as TvaCRUD,
    ValidSymbolsCRUD as VsCRUD,
)


# TEST_PREFIX = "tria-bot:testing"
GLOBAL_PREFIX = "tria_bot"
REDIS_URL = "redis://localhost:6379?decode_responses=True"

pytest_mark_asyncio = pytest.mark.asyncio


# "pytest_mark_sync" causes problem in pytest
def py_test_mark_sync(f):
    return f  # no-op decorator


@pytest.fixture(scope="module")
def event_loop(request):
    loop = None
    policy = asyncio.get_event_loop_policy()
    try:
        loop = policy.new_event_loop()
        policy.set_event_loop(loop)
        yield loop
    finally:
        if loop != None:
            loop.close()


@pytest.fixture(scope="session")
def redis():
    yield get_redis_connection(url=REDIS_URL)


@pytest.fixture(scope="session")
def crud(redis):
    symbols = SymbolsCRUD(conn=redis)
    tva = TvaCRUD(conn=redis)
    vs = VsCRUD(conn=redis)

    # prepare namedtuple
    _names = ["symbols", "top_volume_assets", "valid_symbols"]
    _objs = (symbols, tva, vs)

    return namedtuple("crud", _names)(*_objs)


def _delete_test_keys(prefix: str, conn):
    keys = []
    for key in conn.scan_iter(f"{prefix}:*"):
        keys.append(key)
    if keys:
        conn.delete(*keys)


@pytest.fixture(scope="session", autouse=True)
def cleanup_keys(request):
    # Always use the sync Redis connection with finalizer. Setting up an
    # async finalizer should work, but I'm not suer how yet!
    from redis_om.connections import get_redis_connection as get_sync_redis

    # Increment for every pytest-xdist worker
    conn = get_sync_redis()
    # once_key = f"{TEST_PREFIX}:cleanup_keys"
    once_key = f"{GLOBAL_PREFIX}:cleanup_keys"
    conn.incr(once_key)

    yield

    # Delete keys only once
    if conn.decr(once_key) == 0:
        # _delete_test_keys(TEST_PREFIX, conn)
        _delete_test_keys(GLOBAL_PREFIX, conn)
