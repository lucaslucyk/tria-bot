package tickers

import (
	"log"

	tickers_pkg "github.com/lucaslucyk/tria-bot/pkg/stream/tickers"
	"github.com/lucaslucyk/tria-bot/shared/config"
	"github.com/lucaslucyk/tria-bot/shared/logger"
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
	logger.Init(config.Settings.LogLevel > 0)

	tickers_pkg.Start()
}
