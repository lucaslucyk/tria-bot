from typing import Optional
import anyio
import aiormq
import asyncio
import atexit
from aiormq.abc import DeliveredMessage
from aiormq.connection import Connection
from aiormq.channel import Channel
from datetime import datetime
import orjson


class MessageConsumer:
    def __init__(self, queue_name: str ='command'):
        self._is_alt_working = False
        self.queue_name = queue_name
        self.connection: Optional[Connection] = None
        self.channel: Optional[Channel] = None

        atexit.register(self.close_connection)

    @staticmethod
    def json_or_value(value):
        try:
            return orjson.loads(value)
        except Exception as error:
            # print(error)
            return value

    def close_connection(self):
        if self.connection != None:
            print("Closing connection")
            anyio.run(self.connection.close)

    async def on_message_callback(self, message: DeliveredMessage):
        """
        on_message doesn't necessarily have to be defined as async.
        Here it is to show that it's possible.
        """
        if self._is_alt_working:
            print("currently arbitrating, ignoring message")
            return

        self._is_alt_working = True
        print("Receive message at", datetime.now().isoformat())
        # print(f" [x] Received message {message!r}")
        print(f"Message body is: {self.json_or_value(message.body)}")
        # print("Before sleep!")
        await asyncio.sleep(5)   # Represents async I/O operations
        self._is_alt_working = False


    async def start_consuming(self):
        # Perform connection
        self.connection = await aiormq.connect("amqp://guest:guest@localhost/")

        # Creating a channel
        self.channel = await self.connection.channel()

        # Declaring queue
        declare_ok = await self.channel.queue_declare(self.queue_name, auto_delete=True)
        
        consume_ok = await self.channel.basic_consume(
            declare_ok.queue, self.on_message_callback, no_ack=True
        )
        
        print(f' [*] Waiting for messages. To exit press CTRL+C')

        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            await self.connection.close()

if __name__ == '__main__':
    message_consumer = MessageConsumer()

    # Método asíncrono (no bloqueante)
    anyio.run(message_consumer.start_consuming)

    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(message_consumer.start_consuming())
    # loop.run_forever()
