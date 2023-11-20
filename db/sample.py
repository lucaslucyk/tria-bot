import anyio

from aredis_om import HashModel, NotFoundError
from aredis_om import get_redis_connection

# This Redis instance is tuned for durability.
REDIS_DATA_URL = "redis://localhost:6379"


class Customer(HashModel):
    first_name: str
    last_name: str


class RedisClient:
    def __init__(self, *args, **kwargs):
        pass

    
    async def __aenter__(self):
        self._start_connection()
        return self

    async def __aexit__(self, *args, **kwargs):
        pass

    
    def _start_connection(self):
        Customer.Meta.database = get_redis_connection(
            url=REDIS_DATA_URL,
            decode_responses=True,
        )

    async def save_customer(customer: Customer):
        return await customer.save()

    async def list_customers():
        # To retrieve this customer with its primary key, we use `Customer.get()`:
        return await Customer.all_pks()

    async def get_customer(pk: str):
        # To retrieve this customer with its primary key, we use `Customer.get()`:
        return await Customer.get(pk)

async def main():
    async with RedisClient() as rc:
        # customer = Customer(
        #     first_name="John",
        #     last_name="Doe"
        # )
        # nc = await customer.save()
        async for c in await Customer.all_pks():
            print(c)
        # print(await Customer.all_pks())


if __name__ == "__main__":
    anyio.run(main)