package redis

import (
	"encoding/json"
	"fmt"
	"strings"

	"github.com/redis/go-redis/v9"
)

type DbModel interface {
	DbIndex() int
	Pattern() string
	KeyPrefix() string
	Key() string
}
type Repository[T DbModel] struct {
	db *RedisClient
}

// NewRepository returns a new instance of Repository[T] using the shared RedisClient.
//
// It will panic if the shared RedisClient is not initialized.
func NewRepository[T DbModel]() *Repository[T] {
	return &Repository[T]{
		db: Client,
	}
}

// Save stores the given value in the Redis database.
// The value is serialized to JSON before being saved.
// It returns an error if serialization fails or if there is an issue saving the data.
func (c *Repository[T]) Save(value T) error {
	data, err := json.Marshal(value)
	if err != nil {
		return fmt.Errorf("error serializing value: %w", err)
	}
	return c.db.rdb.Set(c.db.ctx, value.Key(), data, 0).Err()
}

// Get retrieves a value from the Redis database using the provided key.
// It constructs the full key with the predefined prefix from the type T.
// If the key is not found, it returns an error indicating the key is missing.
// If retrieval or deserialization fails, it returns an error detailing the issue.
func (c *Repository[T]) Get(key string) (*T, error) {
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

// Delete removes a value from the Redis database using the provided key.
// It constructs the full key with the predefined prefix from the type T.
// If the key is not found, it returns an error indicating the key is missing.
// If deletion fails, it returns an error detailing the issue.
func (c *Repository[T]) Delete(key string) error {
	return c.db.rdb.Del(c.db.ctx, key).Err()
}

// List returns a map of all the values in the Redis database using the predefined
// prefix from the type T. The map is keyed by the key used to store the value.
// If retrieval or deserialization fails, it returns an error detailing the issue.
func (c *Repository[T]) List() (map[string]*T, error) {
	var t T
	keys, err := c.db.rdb.Keys(c.db.ctx, t.Pattern()).Result()
	if err != nil {
		return nil, fmt.Errorf("error listing keys: %w", err)
	}

	result := make(map[string]*T)
	for _, key := range keys {
		// var value T
		value, err := c.Get(key)
		if err != nil {
			return nil, fmt.Errorf("error reading key %s: %w", key, err)
		}
		result[key] = value
	}

	return result, nil
}

func (c *Repository[T]) Ids(trimPrefix bool) ([]string, error) {
	var t T
	keys, err := c.db.rdb.Keys(c.db.ctx, t.Pattern()).Result()
	if err != nil {
		return []string{}, fmt.Errorf("error listing keys: %w", err)
	}

	result := make([]string, len(keys))
	for i, key := range keys {
		value := key
		if trimPrefix {
			value = strings.TrimPrefix(key, t.KeyPrefix())
		}
		result[i] = value
	}

	return result, nil
}
