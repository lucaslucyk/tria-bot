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
from pydantic import BaseModel
from aredis_om import get_redis_connection, Migrator, RedisModel
from tria_bot.helpers.utils import create_logger
from tria_bot.models.composite import TopAltAssets, Symbol
from tria_bot.clients.composite import AsyncClient


class SocketErrorDetail(BaseModel):
    code: int
    msg: str


class SocketError(Exception):
    ...


ModelType = TypeVar("ModelType", bound=RedisModel)


class CompositeSvc(Generic[ModelType], ABC):
    model: Type[ModelType] = TopAltAssets

    def __init__(self, *args, **kwargs) -> None:
        self._uid = uuid1()
        self.logger = create_logger(f"{type(self).__name__}[{self._uid}]")
        self._redis_url = kwargs.get(
            "redis_om_url",
            os.environ.get("REDIS_OM_URL"),
        )
        self._redis_conn = None
        self._composite_client = None

    async def __aenter__(self) -> "CompositeSvc":
        await Migrator().run()
        self.redis_conn = get_redis_connection(url=self._redis_url)
        self.model.Meta.database = self.redis_conn
        self.model._meta.database = self.redis_conn
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Any] = None,
        exc_val: Optional[Any] = None,
        exc_tb: Optional[Any] = None,
    ) -> None:
        await self.redis_conn.close()

    def _model_or_raise(self, data: Sequence[str]):
        return self.model(assets=data, pk=self.model.Meta.PK_VALUE)

    async def handler(self, data):
        model_data = self._model_or_raise(data=data)
        return await model_data.save()

    async def refresh(self, interval: float = 60.0):
        async with AsyncClient() as composite:
            self.logger.info("Connected to refresh top volume assets.")
            while True:
                data = await composite.get_top_volume_assets()
                result = await self.handler(data=data)
                await asyncio.sleep(interval)


    @classmethod
    async def _refresh(cls, interval: float = 3.0):
        async with cls() as svc:
            await svc.refresh(interval=interval)
