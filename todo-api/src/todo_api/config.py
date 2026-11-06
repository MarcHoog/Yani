from pydantic_settings import BaseSettings, SettingsConfigDict

from yani_shared.auth import AuthSettings


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://yani:yani-dev@localhost:5432/yani"


settings = Settings()
auth_settings = AuthSettings()
