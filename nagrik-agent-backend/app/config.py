"""
Central configuration. Every setting that could differ between dev and demo
(especially LLM provider/model) lives here and ONLY here — nothing else in
the codebase should read raw env vars for these values.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "../.env"), extra="ignore")

    # --- LLM abstraction ---
    llm_provider: str = "gemini"           # "openrouter" | "gemini"
    llm_model: str = "gemini-3.5-flash-lite"
    openrouter_api_key: str = ""
    gemini_api_key: str = ""
    gemini_keys: str = ""

    # --- Sarvam ---
    sarvam_api_key: str = ""
    sarvam_base_url: str = "https://api.sarvam.ai"
    enable_sarvam_fallbacks: bool = True

    # --- Memory / checkpointer ---
    checkpointer_backend: str = "memory"   # "memory" | "redis" | "postgres"
    redis_url: str = "redis://localhost:6379/0"
    postgres_dsn: str = ""

    # --- Person 1 / Person 3 ---
    person1_api_base: str = "http://localhost:8001"
    person3_api_base: str = "http://localhost:8003"
    use_mock_backends: bool = True

    # --- n8n ---
    n8n_webhook_base: str = "http://localhost:5678/webhook"

    # --- Tree-RAG ---
    chroma_persist_dir: str = "./data/chroma_store"
    rag_top_k: int = 5
    rag_candidate_k: int = 10
    rag_similarity_distance_threshold: float = 0.90

    # --- Tavily crawler ---
    tavily_api_key: str = ""


settings = Settings()

