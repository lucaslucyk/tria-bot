from abc import ABC, abstractproperty
import asyncio
import os
from typing import Any, Generic, Iterable, Optional, Type, TypeVar
from binance import AsyncClient, BinanceSocketManager
from binance.streams import ReconnectingWebsocket
from pydantic import BaseModel
from aredis_om import get_redis_connection, Migrator, RedisModel


class SocketErrorDetail(BaseModel):
    code: int
    msg: str


class SocketError(Exception):
    ...

ModelType = TypeVar("ModelType", bound=RedisModel)

class BaseSvc(Generic[ModelType], ABC):

    @abstractproperty
    def model(self) -> Type[ModelType]:
        ...

    @abstractproperty
    def socket_handler_name(self) -> str:
        ...

    def __init__(self, *args, **kwargs):
        self._redis_url = kwargs.get(
            "redis_om_url",
            os.environ.get("REDIS_OM_URL"),
        )
        self._redis_conn = None
        self._binance_client = None
        self._socket_manager = None
        self._socket: Optional[ReconnectingWebsocket] = None

    async def __aenter__(self) -> "BaseSvc":
        await Migrator().run()
        self.redis_conn = get_redis_connection(url=self._redis_url)
        self.model._meta.database = self.redis_conn
        self._binance_client = await AsyncClient.create()
        self._socket_manager = BinanceSocketManager(self._binance_client)
        self._socket_handler = getattr(self._socket_manager, self.socket_handler_name)
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Any] = None,
        exc_val: Optional[Any] = None,
        exc_tb: Optional[Any] = None,
    ) -> None:
        await self.redis_conn.close()
        await self._binance_client.close_connection()

    def _model_or_raise(self, data: Any):
        if isinstance(data, list):
            for t in data:
                yield self.model(**t)

        elif isinstance(data, dict):
            raise SocketError(SocketErrorDetail(**data))
        else:
            raise ValueError("Not supported data")

    async def _save_data(self, data: Iterable[ModelType]):
        for obj in data:
            await obj.save()

    
    async def subscribe(self) -> None:
        self._socket: ReconnectingWebsocket = self._socket_handler()
        async with self._socket as ws:
            while True:
                try:
                    data = self._model_or_raise(await ws.recv())
                    await self._save_data(data=data)
                    await asyncio.sleep(0.001)

                except SocketError as err:
                    print("Error", str(err))
                    await asyncio.sleep(0.1)
                    return await self.subscribe()