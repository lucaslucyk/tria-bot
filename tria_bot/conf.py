from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    USE_STABLE_ASSET: str = "USDT"
    
    # pubsub channels
    PUBSUB_TOP_VOLUME_CHANNEL: str = "top-volume-assets-change"

    # services
    COMPOSITE_LOOP_INTERVAL: float = 60.0

    class Config:
        env_file = '.env'


settings = Settings()