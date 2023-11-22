from redis.asyncio.client import Redis
from abc import ABC, abstractproperty
from typing import Any, Generic, Iterable, Optional, Type, TypeVar
from tria_bot.models.base import HashModelBase
from pydantic import BaseModel

ModelType = TypeVar("ModelType", bound=HashModelBase)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class Decorators:
    @staticmethod
    def use_connection(name: str):
        def decorator(func):
            async def wrapper(crud: CRUDBase, *args, **kwargs):
                conn = kwargs.pop(name, None)
                if conn != None:
                    crud.model._meta.database = kwargs[name]
                return await func(crud, *args, **kwargs)

            return wrapper

        return decorator


class CRUDBase(Generic[ModelType], ABC):
    @abstractproperty
    def model(self) -> Type[ModelType]:
        ...

    @Decorators.use_connection("conn")
    async def get(
        self,
        pk: Any,
        conn: Optional[Redis] = None,
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

    @Decorators.use_connection("conn")
    async def get_all(
        self,
        conn: Optional[Redis] = None,
    ):
        async for pk in self.model.all_pks():
            yield await self.get(pk=pk)
