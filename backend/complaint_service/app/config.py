import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/nagrik_complaints"
    
    LLM_PROVIDER: str = "openrouter"
    LLM_MODEL: str = "google/gemini-2.0-flash-001"
    OPENROUTER_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    FAISS_INDEX_PATH: str = "data/faiss_index"
    
    N8N_WEBHOOK_URL: str = ""
    
    DEFAULT_ACK_SLA_HOURS: int = 24
    DEFAULT_RESOLUTION_SLA_HOURS: int = 168
    SLA_CHECK_INTERVAL_MINUTES: int = 15
    
    DUPLICATE_SIMILARITY_THRESHOLD: float = 0.80
    DUPLICATE_CATEGORY_BOOST: float = 0.15

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
