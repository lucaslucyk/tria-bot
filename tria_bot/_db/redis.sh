#!/bin/bash

sudo docker run -it --rm --name redisstack --net="host" -p 6379:6379 -p 8001:8001 redis/redis-stack