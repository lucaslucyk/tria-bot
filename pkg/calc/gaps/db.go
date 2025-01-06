package gaps

import (
	"sync"

	dbm "github.com/lucaslucyk/tria-bot/shared/models/db"
	"github.com/lucaslucyk/tria-bot/shared/redis"
)

var (
	SymbolsRepo *redis.Repository[dbm.Symbol]
	GapsRepo    *redis.Repository[dbm.Gap]
	TickersRepo *redis.Repository[dbm.Ticker]
	once        sync.Once
)

func InitRepos() {
	once.Do(func() {
		GapsRepo = redis.NewRepository[dbm.Gap]()
		SymbolsRepo = redis.NewRepository[dbm.Symbol]()
		TickersRepo = redis.NewRepository[dbm.Ticker]()
	})
}
