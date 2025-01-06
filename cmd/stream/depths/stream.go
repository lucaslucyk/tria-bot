package depths

import (
	depths_pkg "github.com/lucaslucyk/tria-bot/pkg/stream/depths"
)

func Start() {
	// start ticker service
	depths_pkg.Start()
}
