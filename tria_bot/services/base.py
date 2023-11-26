from abc import ABC, abstractproperty
import asyncio
import os
from inspect import isawaitable
from typing import (
    Any,
    Generator,
    Generic,
    Optional,
    Type,
    TypeVar,
)
from uuid import uuid1
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


class BaseSvc():

    def __init__(self, *args, **kwargs) -> None:
        self._uid = uuid1()
        self.logger = create_logger(f"{type(self).__name__}[{self._uid}]")
        self._redis_url = kwargs.get(
            "redis_om_url",
            os.environ.get("REDIS_OM_URL"),
        )
        self._redis_conn = None

    async def __aenter__(self) -> "BaseSvc":
        self._redis_conn = get_redis_connection(url=self._redis_url)
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Any] = None,
        exc_val: Optional[Any] = None,
        exc_tb: Optional[Any] = None,
    ) -> None:
        if self._redis_conn != None:
            await self._redis_conn.close()


class SocketBaseSvc(Generic[ModelType], ABC):
    @abstractproperty
    def model(self) -> Type[ModelType]:
        ...

    @abstractproperty
    def socket_handler_name(self) -> str:
        ...

    def __init__(self, *args, **kwargs) -> None:
        self._uid = uuid1()
        self.logger = create_logger(f"{type(self).__name__}[{self._uid}]")
        self._redis_url = kwargs.get(
            "redis_om_url",
            os.environ.get("REDIS_OM_URL"),
        )
        self._redis_conn = None
        self._binance_client = None
        self._socket_manager = None
        self._socket: Optional[ReconnectingWebsocket] = None
        self._is_running: bool = True

    async def __aenter__(self) -> "SocketBaseSvc":
        await Migrator().run()
        self._redis_conn = get_redis_connection(url=self._redis_url)
        self.model.Meta.database = self._redis_conn
        self.model._meta.database = self._redis_conn
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
        self.logger.info("Stopping service...")
        await self._redis_conn.close()
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

    async def callback(self, stream: Any) -> Any:
        """Save received stream from API and store in database

        Args:
            stream (Any): API received data

        Returns:
            Any: Store result
        """
        model_sequence = self._model_or_raise(data=stream)
        return await self.model.add(models=list(model_sequence))

    async def ws_subscribe(self, **params) -> None:
        """Subscribe to a model socket and pass result to `self.callback`"""
        self._socket: ReconnectingWebsocket = self._socket_handler(**params)
        async with self._socket as ws:
            msg = "Connected to `{sn}`{opt}.".format(
                sn=self.socket_handler_name,
                opt=f" with {params}" if params else "",
            )
            self.logger.info(msg)
            while self._is_running:
                try:
                    stream = await ws.recv()
                    result = self.callback(stream=stream)
                    if isawaitable(result):
                        await result

                    await asyncio.sleep(0.001)

                except SocketError as err:
                    if self._is_running:
                        self.logger.error(f"Socket error: {err}.\nReconnecting...")
                        await asyncio.sleep(0.1)
                        return await self.subscribe()
