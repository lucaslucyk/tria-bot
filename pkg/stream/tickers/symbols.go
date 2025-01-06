package tickers

import (
	"time"

	"github.com/lucaslucyk/tria-bot/shared/logger"
	dbm "github.com/lucaslucyk/tria-bot/shared/models/db"
	"github.com/lucaslucyk/tria-bot/shared/redis"
)

func GetSymbols() ([]string, error) {
	logger.Info("Getting symbols from db...")
	sr := redis.NewRepository[dbm.Symbol]()
	s, err := sr.Ids(true)
	if err != nil {
		return s, err
	}
	if len(s) == 0 {
		logger.Info("No symbols yet, trying again in 3 seconds...")
		time.Sleep(3 * time.Second)
		return GetSymbols()
	}
	return s, nil
}
