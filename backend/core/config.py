from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""
    gemini_api_key: str = ""
    database_url: str = "sqlite:///./nagrik.db"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
