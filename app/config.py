from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    rss_url: str 
    poll_interval_seconds: int = 60
    telegram_bot_token: str
    telegram_chat_id: str
    database_url: str = "sqlite:///./feed.db"

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')
