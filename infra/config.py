from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # GitHub
    github_token: str
    github_webhook_secret: str = "changeme"
    github_url: str = "https://api.github.com"
    
    # App
    app_base_url: str = "http://localhost:8000"
    
    # Database
    database_url: str = "postgresql+psycopg2://prpoints:prpoints@localhost:5432/prpoints"
    
    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: str = "6333"
    qdrant_collection: str = "normativos"
    
    # LLM
    llm_provider: str = "ollama"
    ollama_model: str = "llama3.1:8b"
    openai_api_key: Optional[str] = None
    openai_model: Optional[str] = "gpt-4o-mini"

    class Config:
        env_file = ".env"

settings = Settings()