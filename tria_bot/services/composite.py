from abc import ABC, abstractproperty
import asyncio
import os
from inspect import isawaitable
from typing import (
    Any,
    Generator,
    Generic,
    Optional,
    Sequence,
    Type,
    TypeVar,
)
from uuid import uuid1
import orjson
from pydantic import BaseModel
from aredis_om import get_redis_connection, Migrator, RedisModel, NotFoundError
from tria_bot.conf import settings
from tria_bot.helpers.utils import create_logger
from tria_bot.models.composite import TopVolumeAssets, Symbol
from tria_bot.clients.composite import AsyncClient


class SocketErrorDetail(BaseModel):
    code: int
    msg: str


class SocketError(Exception):
    ...


ModelType = TypeVar("ModelType", bound=RedisModel)


class CompositeSvc(Generic[ModelType], ABC):
    loop_interval: float = settings.COMPOSITE_LOOP_INTERVAL
    model: Type[ModelType] = TopVolumeAssets
    TOP_VOLUME_CHANGE_EVENT = "top-volume-change"

    def __init__(self, *args, **kwargs) -> None:
        self._uid = uuid1()
        self.logger = create_logger(f"{type(self).__name__}[{self._uid}]")
        self._redis_url = kwargs.get(
            "redis_om_url",
            os.environ.get("REDIS_OM_URL"),
        )
        self._redis_conn = None
        self._composite_client = None
        self._is_running: bool = True

    async def __aenter__(self) -> "CompositeSvc":
        await Migrator().run()
        self._redis_conn = get_redis_connection(url=self._redis_url)
        self.model.Meta.database = self._redis_conn
        self.model._meta.database = self._redis_conn
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Any] = None,
        exc_val: Optional[Any] = None,
        exc_tb: Optional[Any] = None,
    ) -> None:
        await self._redis_conn.close()

    def _model_or_raise(self, data: Sequence[str]):
        return self.model(assets=data, pk=self.model.Meta.PK_VALUE)

    async def _db_or_empty(self) -> TopVolumeAssets:
        try:
            return await self.model.get(self.model.Meta.PK_VALUE)
        except NotFoundError:
            return self.model(assets=[""], pk=self.model.Meta.PK_VALUE)

    async def on_change_handler(self, old: Sequence[str], new: Sequence[str]):
        msg = f"Top volume assets change from {old} to {new}"
        self.logger.info(msg)
        data = {
            "event": self.TOP_VOLUME_CHANGE_EVENT,
            "old": old,
            "new": new
        }
        await self._redis_conn.publish(
            settings.PUBSUB_TOP_VOLUME_CHANNEL,
            orjson.dumps(data),
        )

    async def handler(self, data: Sequence[str]):
        model_data = await self._db_or_empty()
        if set(model_data.assets) != set(data):
            await self.on_change_handler(old=model_data.assets, new=data)

            # save data
            model_data.assets = data
            await model_data.save()

    async def refresh(self, interval: Optional[float] = None):
        async with AsyncClient() as composite:
            self.logger.info("Connected to Binance API to get Top Assets.")
            while self._is_running:
                data = await composite.get_top_volume_assets()
                await self.handler(data=data)
                await asyncio.sleep(interval or self.loop_interval)

    @classmethod
    async def _refresh(cls, interval: float = 3.0):
        async with cls() as svc:
            await svc.refresh(interval=interval)
