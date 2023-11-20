#!/bin/bash

sudo docker run -it --rm --name redisstack -p 16379:6379 -p 8001:8001 redis/redis-stack