from pydantic_settings import BaseSettings, SettingsConfigDict

from yani_shared.auth import AuthSettings


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "yani-dev"
    # Customer mapping lives in todo-api (customer_tenants); resolved via its /api/v1/me.
    todo_api_url: str = "http://localhost:8010"
    customer_cache_seconds: int = 300


settings = Settings()
auth_settings = AuthSettings()
