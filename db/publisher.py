import anyio
from models import Customer


async def main():
    customer = Customer(
        first_name="John2",
        last_name="Doe2"
    )
    nc = await customer.save()
    print("new customer saved", nc)


if __name__ == "__main__":
    anyio.run(main)