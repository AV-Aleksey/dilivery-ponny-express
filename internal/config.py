from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    LOG_LEVEL: str = "INFO"

    PONY_API_KEY: str
    PONY_API_URL: str

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
