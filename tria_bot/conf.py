from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    USE_STABLE_ASSET: str = "USDT"

    # exchange
    EXCHANGE_FEE: float = .001
    
    # pubsub channels
    PUBSUB_TOP_VOLUME_CHANNEL: str = "top-volume-assets-change"
    PUBSUB_PROFFIT_CHANNEL: str = "proffit-detection"
    PUBSUB_GAPS_CHANNEL: str = "gaps-detection"
    #PUBSUB_GAPS_CHANNEL: str = "gaps-calc"

    # services
    COMPOSITE_LOOP_INTERVAL: float = 60.0
    GAP_MIN: float = 3.0
    PROFFIT_PERCENT_FORMAT: bool = True
    MIN_PROFFIT_DETECT: float = .3  # percent
    PROFFIT_INDEX: int = 0

    class Config:
        extra = "ignore"
        env_file = '.env'


settings = Settings()