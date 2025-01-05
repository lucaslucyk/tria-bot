package common

import (
	"log"

	"github.com/lucaslucyk/tria-bot/shared/config"
	"github.com/lucaslucyk/tria-bot/shared/logger"
	"github.com/lucaslucyk/tria-bot/shared/redis"
)

func Start() {
	log.Println("starting stream...")

	if _, err := config.Load(); err != nil {
		log.Fatal(err)
		panic(err)
	} else {
		log.Println("loaded config")
	}

	// start logger
	logger.Init(config.Settings.Debug)

	// init redis client
	redis.Init(
		config.Settings.RedisAddress,
		config.Settings.RedisPassword,
		config.Settings.RedisDefaultDb,
	)
	// defer redis.Close()
}
