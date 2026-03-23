from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    debug: bool

    database_url: str
    redis_url: str
    bot_token: str
    owner_id: int

    support_link: str
    channel_description_link: str
