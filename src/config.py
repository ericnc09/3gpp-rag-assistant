"""
Configuration management for 3GPP RAG Assistant
"""
from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = ConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    # Ollama Configuration (local LLM - no API key needed)
    ollama_base_url: str = "http://localhost:11434"
    llm_model: str = "llama3.2"
    max_tokens: int = 1000
    temperature: float = 0.1

    # Embedding Configuration (local sentence-transformers - no API key needed)
    embedding_model: str = "bge-small"  # options: mini, mpnet, bge-small, bge-base

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


# Global settings instance
settings = Settings()
