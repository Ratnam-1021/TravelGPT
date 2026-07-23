import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "TravelGPT – AI Trip Planner"
    DEBUG: bool = True
    
    # API Keys
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    
    # Model Configurations
    DEFAULT_PROVIDER: str = os.getenv("DEFAULT_PROVIDER", "groq") # groq | openai | anthropic
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    
    # Chroma Vector DB Settings
    CHROMA_DB_DIR: str = os.path.join(os.path.dirname(__file__), "../chroma_db")
    DATA_DIR: str = os.path.join(os.path.dirname(__file__), "data")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
