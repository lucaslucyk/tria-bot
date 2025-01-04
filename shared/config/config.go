package config

import (
	"log"
	"sync"

	"github.com/spf13/viper"
)

type Config struct {
	LogLevel int
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

	// load from file
	once.Do(func() {
		if err := viper.ReadInConfig(); err != nil {
			log.Printf("Error reading config file: %v", err)
		}
	})

	Settings = &Config{
		LogLevel: viper.GetInt("LOG_LEVEL"),
	}

	return Settings, nil
}
