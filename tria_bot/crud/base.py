import asyncio
from redis.asyncio.client import Redis
from abc import ABC, abstractproperty
from typing import Any, Generic, Iterable, Optional, Sequence, Type, TypeVar
#from tria_bot.models.base import HashModelBase
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

    
    def __init__(self, conn: Optional[redis.Redis]) -> None:
        super().__init__()
        self._conn = conn
        if self._conn == None:
            self._conn = get_redis_connection()
        
        self.model.Meta.database = self._conn
        self.model._meta.database = self._conn


    # @Decorators.use_connection("conn")
    async def get(
        self,
        pk: Any,
        # conn: Optional[Redis] = None,
    ) -> Optional[ModelType]:
        """Get row from model by uid

        Args:
            db (AsyncSession): Async db session
            uid (UUID): UUID to filter

        Returns:
            Optional[ModelType]: ModelType instance or None if id not exists
        """
        # if conn != None:
        #     self.model._meta.database = conn
        return await self.model.get(pk=pk)


    async def wait_for(self, pk: Any) -> ModelType:
        try:
            return await self.get(pk=pk)
        except NotFoundError:
            await asyncio.sleep(1.0)
            return self.wait_for(pk=pk)

    # @Decorators.use_connection("conn")
    async def get_all(
        self,
        # conn: Optional[Redis] = None,
    ):
        async for pk in self.model.all_pks():
            yield await self.get(pk=pk)

    async def add(
        self,
        models: Sequence[ModelType]
    ):
        return await self.model.add(models=models)