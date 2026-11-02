from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///backend/storage/cad2bom.db"
    storage_dir: str = "backend/storage"
    api_base_url: str = "http://localhost:8000/api/v1"


settings = Settings()
