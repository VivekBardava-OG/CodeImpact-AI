from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
import os

class Settings(BaseSettings):
    # FalkorDB Graph Database
    falkordb_host: str = Field(default="127.0.0.1", alias="FALKORDB_HOST")
    falkordb_port: int = Field(default=6379, alias="FALKORDB_PORT")
    falkordb_password: Optional[str] = Field(default=None, alias="FALKORDB_PASSWORD")
    
    # Server configuration
    host: str = Field(default="127.0.0.1", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    debug: bool = Field(default=True, alias="DEBUG")
    
    # Ingestion constraints & security
    max_file_size_mb: int = Field(default=15, alias="MAX_FILE_SIZE_MB")
    max_file_count: int = Field(default=500, alias="MAX_FILE_COUNT")
    max_zip_size_mb: int = Field(default=25, alias="MAX_ZIP_SIZE_MB")
    temp_dir: str = Field(default="temp_repos")
    
    # AI Explanation (optional)
    gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")
    llm_model: str = Field(default="gemini-1.5-flash", alias="LLM_MODEL")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
