package config

import (
	"log"
	"sync"

	"github.com/spf13/viper"
)

type Config struct {
	LogLevel int

	// redis
	RedisAddress   string
	RedisPassword  string
	RedisTickersDb int
}

var (
	once     sync.Once
	Settings *Config
)

func Load() (*Config, error) {
	viper.SetConfigFile(".env")
	viper.AutomaticEnv()

	// define default values
	viper.SetDefault("LOG_LEVEL", "0")

	// redis
	viper.SetDefault("REDIS_ADDRESS", "localhost:6379")
	viper.SetDefault("REDIS_PASSWORD", "")
	viper.SetDefault("REDIS_TICKERS_DB", "0")

	// load from file
	once.Do(func() {
		if err := viper.ReadInConfig(); err != nil {
			log.Printf("Error reading config file: %v", err)
		}
	})

	Settings = &Config{
		LogLevel:       viper.GetInt("LOG_LEVEL"),
		RedisTickersDb: viper.GetInt("REDIS_TICKERS_DB"),
		RedisAddress:   viper.GetString("REDIS_ADDRESS"),
		RedisPassword:  viper.GetString("REDIS_PASSWORD"),
	}

	return Settings, nil
}
