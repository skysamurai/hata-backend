from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://hata:hata@localhost:5432/hata"
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    PARSER_INTERVAL_MINUTES: int = 5
    AGENT_SCORE_THRESHOLD: int = 60
    AVITO_API_KEY: str = ""
    FIRST_REGION: str = "kazan"

    class Config:
        env_file = ".env"

settings = Settings()
