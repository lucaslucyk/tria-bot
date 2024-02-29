# Tria Bot
Triangle bot for Binance exchange


> [!WARNING]
> This project is currently on Development phase

## Quick start

Clone repository and use `Docker` with `docker-compose` to build and run images.

1. Clone repository

```shell
git clone https://github.com/lucaslucyk/tria-bot.git
```

2. Create .env file with your config

```ini
REDIS_OM_URL="redis://tria-redis:6379?decode_responses=True"
REDIS_DATA_URL="redis://tria-redis:6379?decode_responses=True"
REDIS_PUB_SUB_URL="redis://tria-redis:6379?decode_responses=True"
BINANCE_API_KEY="{your-binance-api-key}"
BINANCE_API_SECRET="{your-binance-api-secret}"
```

3. Start containers with `docker-compose`.

```shell
docker-compose up -d
```


## Test application

To run tests, use the utility script.

```shell
sh script/tests.sh
```

## Contributions and Feedback

I would love to receive contributions and feedback! If you'd like to get involved, please contact me through one of the contact methods in my Profile.

## License
This project is licensed under the terms of the MIT license.