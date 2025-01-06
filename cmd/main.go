package main

import (
	"flag"
	"log"

	"github.com/lucaslucyk/tria-bot/cmd/api/symbols"
	"github.com/lucaslucyk/tria-bot/cmd/common"
	"github.com/lucaslucyk/tria-bot/cmd/stream/depths"
	"github.com/lucaslucyk/tria-bot/cmd/stream/tickers"
	"github.com/lucaslucyk/tria-bot/shared/redis"
)

func main() {
	service := flag.String("service", "", "service to start")
	flag.Parse()

	log.Println("starting service...")
	common.Start()
	defer redis.Close()

	switch *service {
	case "tickers":
		tickers.Start()
	case "depths":
		depths.Start()
	case "symbols":
		symbols.Start()
	default:
		log.Fatal("service not found")
	}
}
