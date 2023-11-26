from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    USE_STABLE_ASSET: str = "USDT"

    # binance
    BINANCE_FEE_MULTIPLIER: float = .999
    
    # pubsub channels
    PUBSUB_TOP_VOLUME_CHANNEL: str = "top-volume-assets-change"

    # services
    COMPOSITE_LOOP_INTERVAL: float = 60.0
    GAP_MIN: float = 1.5
    PROFFIT_MIN: float = .3

    class Config:
        extra = "ignore"
        env_file = '.env'


settings = Settings()