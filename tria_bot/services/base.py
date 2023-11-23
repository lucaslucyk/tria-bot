from abc import ABC, abstractproperty
import asyncio
import os
from typing import (
    Any,
    Generator,
    Generic,
    Iterable,
    Optional,
    Type,
    TypeVar,
)
from binance import AsyncClient, BinanceSocketManager
from binance.streams import ReconnectingWebsocket
from pydantic import BaseModel
from aredis_om import get_redis_connection, Migrator, RedisModel
from tria_bot.helpers.utils import create_logger


class SocketErrorDetail(BaseModel):
    code: int
    msg: str


class SocketError(Exception):
    ...


ModelType = TypeVar("ModelType", bound=RedisModel)


class SocketBaseSvc(Generic[ModelType], ABC):
    @abstractproperty
    def model(self) -> Type[ModelType]:
        ...

    @abstractproperty
    def socket_handler_name(self) -> str:
        ...

    def __init__(self, *args, **kwargs) -> None:
        self.logger = create_logger(type(self).__name__)
        self._redis_url = kwargs.get(
            "redis_om_url",
            os.environ.get("REDIS_OM_URL"),
        )
        self._redis_conn = None
        self._binance_client = None
        self._socket_manager = None
        self._socket: Optional[ReconnectingWebsocket] = None

    async def __aenter__(self) -> "SocketBaseSvc":
        await Migrator().run()
        self.redis_conn = get_redis_connection(url=self._redis_url)
        self.model.Meta.database = self.redis_conn
        self.model._meta.database = self.redis_conn
        self._binance_client = await AsyncClient.create()
        self._socket_manager = BinanceSocketManager(self._binance_client)
        self._socket_handler = getattr(
            self._socket_manager, self.socket_handler_name
        )
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Any] = None,
        exc_val: Optional[Any] = None,
        exc_tb: Optional[Any] = None,
    ) -> None:
        await self.redis_conn.close()
        await self._binance_client.close_connection()

    def _model_or_raise(
        self,
        data: Any,
    ) -> Generator[ModelType, Any, None]:
        """Try to create a list of Model instance

        Args:
            data (Any): Binance socket received data

        Raises:
            SocketError: If received data is an error
            ValueError: If receive an unsopported type

        Yields:
            Generator[ModelType, Any, None]: Model instance
        """
        if isinstance(data, list):
            for obj in data:
                yield self.model(**obj)

        elif isinstance(data, dict):
            try:
                yield self.model(**data)
            except:
                raise SocketError(SocketErrorDetail(**data))
        else:
            raise ValueError("Not supported data")

    async def _save_data(
        self, data: Iterable[ModelType]
    ) -> None:
        """Save data into database

        Args:
            data (Iterable[ModelType]: Iterable model
        """
        for obj in data:
            await obj.save()

    async def subscribe(self, **params) -> None:
        """Subscribe to a model socket and save results on Redis database"""
        self._socket: ReconnectingWebsocket = self._socket_handler(**params)
        async with self._socket as ws:
            self.logger.info(f"Connected to {self.socket_handler_name} socket.")
            while True:
                try:
                    stream = await ws.recv()
                    data = self._model_or_raise(data=stream)
                    await self._save_data(data=data)
                    await asyncio.sleep(0.001)

                except SocketError as err:
                    self.logger.error(f"Socket error: {err}.\nReconnecting...")
                    await asyncio.sleep(0.1)
                    return await self.subscribe()
