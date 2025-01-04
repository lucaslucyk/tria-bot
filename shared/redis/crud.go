package redis

import (
	"encoding/json"
	"fmt"

	"github.com/redis/go-redis/v9"
)

type DbModel interface {
	DbIndex() int
	Pattern() string
	Key() string
}
type Repository[T DbModel] struct {
	db *RedisClient
}

func NewRepository[T DbModel]() *Repository[T] {
	return &Repository[T]{
		db: Client,
	}
}

func (c *Repository[T]) Save(value T) error {
	data, err := json.Marshal(value)
	if err != nil {
		return fmt.Errorf("error serializing value: %w", err)
	}
	return c.db.rdb.Set(c.db.ctx, value.Key(), data, 0).Err()
}

func (c *Repository[T]) Read(key string) (*T, error) {
	data, err := c.db.rdb.Get(c.db.ctx, key).Result()
	if err == redis.Nil {
		return nil, fmt.Errorf("key not found: %s", key)
	} else if err != nil {
		return nil, fmt.Errorf("error retrieving key: %w", err)
	}
	out := new(T)
	if err := json.Unmarshal([]byte(data), out); err != nil {
		return nil, fmt.Errorf("error unmarshalling value: %w", err)
	}
	return out, nil
}

// Delete removes an object from Redis
func (c *Repository[T]) Delete(key string) error {
	return c.db.rdb.Del(c.db.ctx, key).Err()
}

// List retrieves all keys matching a pattern and their values
func (c *Repository[T]) List() (map[string]*T, error) {
	var t T
	keys, err := c.db.rdb.Keys(c.db.ctx, t.Pattern()).Result()
	if err != nil {
		return nil, fmt.Errorf("error listing keys: %w", err)
	}

	result := make(map[string]*T)
	for _, key := range keys {
		// var value T
		value, err := c.Read(key)
		if err != nil {
			return nil, fmt.Errorf("error reading key %s: %w", key, err)
		}
		result[key] = value
	}

	return result, nil
}
