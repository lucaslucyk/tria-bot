from redis.asyncio.client import Redis
from abc import ABC, abstractproperty
from typing import Generic, Optional, Type, TypeVar
from tria_bot.models.base import HashModelBase
from pydantic import BaseModel

ModelType = TypeVar("ModelType", bound=HashModelBase)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType], ABC):
    @abstractproperty
    def model(self) -> Type[ModelType]:
        ...

    async def get(
        self, pk: str, conn: Optional[Redis] = None
    ) -> Optional[ModelType]:
        """Get row from model by uid

        Args:
            db (AsyncSession): Async db session
            uid (UUID): UUID to filter

        Returns:
            Optional[ModelType]: ModelType instance or None if id not exists
        """
        if conn != None:
            self.model._meta.database = conn

        return await self.model.get(pk=pk)
