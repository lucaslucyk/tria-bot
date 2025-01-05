package config

import (
	"log"
	"strings"
	"sync"

	"github.com/spf13/viper"
)

type Config struct {
	Debug bool

	// redis
	RedisAddress   string
	RedisPassword  string
	RedisDefaultDb int

	// coins
	StableCoin  string
	StrongCoins []string
	AltCoins    []string
}

var (
	once     sync.Once
	Settings *Config
)

func Load() (*Config, error) {
	viper.SetConfigFile(".env")
	viper.AutomaticEnv()

	// define default values
	viper.SetDefault("DEBUG", "0")

	// redis
	viper.SetDefault("REDIS_ADDRESS", "localhost:6379")
	viper.SetDefault("REDIS_PASSWORD", "")
	viper.SetDefault("REDIS_DEFAULT_DB", "0")

	// coins
	viper.SetDefault("STABLE_COIN", "USDT")
	viper.SetDefault("STRONG_COINS", "BTC,ETH,BNB")

	// load from file
	once.Do(func() {
		if err := viper.ReadInConfig(); err != nil {
			log.Printf("Error reading config file: %v", err)
		}
	})

	Settings = &Config{
		Debug: viper.GetBool("DEBUG"),

		// redis
		RedisDefaultDb: viper.GetInt("REDIS_DEFAULT_DB"),
		RedisAddress:   viper.GetString("REDIS_ADDRESS"),
		RedisPassword:  viper.GetString("REDIS_PASSWORD"),

		// coins
		StableCoin:  viper.GetString("STABLE_COIN"),
		StrongCoins: strings.Split(viper.GetString("STRONG_COINS"), ","),
		AltCoins:    strings.Split(viper.GetString("ALT_COINS"), ","),
	}

	return Settings, nil
}
