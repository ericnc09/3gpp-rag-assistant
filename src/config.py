"""
Configuration management for 3GPP RAG Assistant
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # OpenAI Configuration
    openai_api_key: str
    embedding_model: str = "text-embedding-3-small"
    llm_model: str = "gpt-4o-mini"
    max_tokens: int = 1000
    temperature: float = 0.1
    
    # Vector Database Configuration
    vector_db_path: str = "./data/vectordb"
    collection_name: str = "3gpp_specs"
    
    # Document Processing
    chunk_size: int = 1000
    chunk_overlap: int = 200
    data_dir: str = "./data/raw"
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"
    
    # Application Settings
    max_history_length: int = 5
    top_k_results: int = 5
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
