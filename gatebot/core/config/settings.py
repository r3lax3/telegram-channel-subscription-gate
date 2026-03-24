from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    debug: bool = False

    database_url: str
    redis_url: str
    bot_token: str
    owner_ids: list[int]

    support_link: str
    channel_description_link: str = ""

    channel_id: int
    subscription_price: int = 1234
    subscription_days: int = 30

    prodamus_api_key: str = ""
    prodamus_domain: str = ""
    prodamus_secret_key: str = ""

    webhook_host: str = ""
    webhook_port: int = 8080
