package utils

import "github.com/lucaslucyk/tria-bot/shared/config"

type AssetKind string

const (
	StableCoin AssetKind = "stable"
	StrongCoin AssetKind = "strong"
	AltCoin    AssetKind = "alternative"
)

func IsStrongAsset(asset string) bool {
	for _, coin := range config.Settings.StrongCoins {
		if asset == coin {
			return true
		}
	}
	return false
}

func IsStableAsset(asset string) bool {
	return asset == config.Settings.StableCoin
}

func IsAltAsset(asset string) bool {
	return !IsStableAsset(asset) && !IsStrongAsset(asset)
}

func GetAssetKind(asset string) AssetKind {
	if IsStableAsset(asset) {
		return StableCoin
	} else if IsStrongAsset(asset) {
		return StrongCoin
	} else {
		return AltCoin
	}
}
