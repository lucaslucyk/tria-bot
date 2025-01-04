package redis

import (
	"context"
	"sync"

	"github.com/lucaslucyk/tria-bot/shared/logger"
	"github.com/redis/go-redis/v9"
)

var (
	once   sync.Once
	Client *RedisClient
)

type RedisClient struct {
	rdb *redis.Client
	ctx context.Context
}

func NewClient(address, password string, db int) *RedisClient {
	return &RedisClient{
		rdb: redis.NewClient(&redis.Options{
			Addr:     address,
			Password: password,
			DB:       db,
		}),
		ctx: context.Background(),
	}
}

func Init(address, password string, db int) {
	once.Do(func() {
		Client = NewClient(address, password, db)
	})
}

func Close() {
	if Client == nil {
		return
	}

	logger.Info("Closing Redis client...")
	Client.rdb.FlushAll(Client.ctx)
	if err := Client.rdb.Close(); err != nil {
		logger.Error("Error closing Redis client: %v", err)
	}
	logger.Info("Redis client closed successfully!")
}
