import asyncio
from redis.asyncio.client import Redis
from abc import ABC, abstractproperty
from typing import (
    Any,
    AsyncGenerator,
    Generic,
    Iterable,
    Optional,
    Sequence,
    Type,
    TypeVar,
)

# from tria_bot.models.base import HashModelBase
from aredis_om import RedisModel, get_redis_connection, NotFoundError
from aredis_om.connections import redis
from pydantic import BaseModel

ModelType = TypeVar("ModelType", bound=RedisModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class Decorators:
    @staticmethod
    def use_connection(name: str):
        def decorator(func):
            async def wrapper(crud: "CRUDBase", *args, **kwargs):
                conn = kwargs.pop(name, None)
                if conn != None:
                    crud.model.Meta.database = conn
                    crud.model._meta.database = conn
                return await func(crud, *args, **kwargs)

            return wrapper

        return decorator


class CRUDBase(Generic[ModelType], ABC):
    @abstractproperty
    def model(self) -> Type[ModelType]:
        ...

    def __init__(self, conn: Optional[redis.Redis] = None) -> None:
        super().__init__()
        self._conn = conn
        if self._conn == None:
            self._conn = get_redis_connection()

        self.model.Meta.database = self._conn
        self.model._meta.database = self._conn

    async def __aenter__(self) -> "CRUDBase":
        if self._conn == None:
            self._conn = get_redis_connection()
        return self

    
    async def __aexit__(
        self,
        exc_type: Optional[Any] = None,
        exc_val: Optional[Any] = None,
        exc_tb: Optional[Any] = None,
    ) -> None:
        if self._conn != None:
            await self._conn.close()


    async def save(self, obj: ModelType):
        return await obj.save()

    async def get(self, pk: Any) -> Optional[ModelType]:
        """Get row from model by uid

        Args:
            db (AsyncSession): Async db session
            uid (UUID): UUID to filter

        Returns:
            Optional[ModelType]: ModelType instance or None if id not exists
        """
        return await self.model.get(pk=pk)

    async def wait_for(self, pk: Any) -> ModelType:
        try:
            return await self.get(pk=pk)
        except NotFoundError:
            await asyncio.sleep(1.0)
            return await self.wait_for(pk=pk)

    async def all_pks(self) -> AsyncGenerator[Any, None]:
        async for pk in self.model.all_pks():
            yield pk

    async def get_all(self) -> AsyncGenerator[ModelType, None]:
        async for pk in self.model.all_pks():
            yield await self.get(pk=pk)

    async def add(self, models: Sequence[ModelType]) -> Sequence[ModelType]:
        return await self.model.add(models=models)
