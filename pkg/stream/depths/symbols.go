package depths

import (
	dbm "github.com/lucaslucyk/tria-bot/shared/models/db"
	"github.com/lucaslucyk/tria-bot/shared/redis"
)

func GetSymbols() ([]string, error) {
	sr := redis.NewRepository[dbm.Symbol]()
	return sr.Ids(true)
}
