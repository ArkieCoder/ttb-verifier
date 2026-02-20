"""
Configuration management for TTB Label Verifier API.

Uses pydantic-settings to load and validate environment variables
from .env files and system environment.
"""

import json
from typing import List
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Ollama Configuration
    ollama_host: str = Field(
        default="http://ollama:11434",
        description="Ollama API endpoint for AI OCR"
    )
    ollama_model: str = Field(
        default="llama3.2-vision",
        description="Ollama vision model for label OCR"
    )
    ollama_timeout_seconds: int = Field(
        default=60,
        description="Timeout for Ollama OCR requests in seconds"
    )
    
    # App Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    max_file_size_mb: int = Field(
        default=10,
        description="Maximum file size for uploads in megabytes"
    )
    max_batch_size: int = Field(
        default=50,
        description="Maximum number of images in a batch request"
    )
    
    # Job Management Configuration
    job_retention_hours: int = Field(
        default=1,
        description="Hours to retain completed batch jobs before cleanup"
    )
    job_cleanup_interval_seconds: int = Field(
        default=3600,
        description="Interval between job cleanup runs in seconds (default: 1 hour)"
    )

    # Async single-image queue configuration
    queue_db_path: str = Field(
        default="/app/tmp/queue.db",
        description="Path to the SQLite queue database (shared volume)"
    )
    queue_max_attempts: int = Field(
        default=3,
        description="Maximum processing attempts per queued verify job before permanent failure"
    )
    worker_ollama_timeout_seconds: int = Field(
        default=12,
        description="Per-attempt Ollama timeout used by the worker process (seconds)"
    )
    
    # CORS Configuration
    cors_origins: str = Field(
        default='["*"]',
        description="JSON array of allowed CORS origins"
    )
    
    # UI Configuration
    allowed_hosts: str = Field(
        default='["localhost", "127.0.0.1", "testserver"]',
        description="JSON array of allowed hostnames for UI access"
    )
    domain_name: str = Field(
        default="",
        description="Primary domain name for the application (e.g., 'ttb-verifier.example.com')"
    )
    
    # Model configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @field_validator("max_file_size_mb")
    @classmethod
    def validate_max_file_size(cls, v: int) -> int:
        """Ensure max file size is positive."""
        if v <= 0:
            raise ValueError("max_file_size_mb must be positive")
        if v > 100:
            raise ValueError("max_file_size_mb should not exceed 100MB for practical use")
        return v
    
    @field_validator("max_batch_size")
    @classmethod
    def validate_max_batch_size(cls, v: int) -> int:
        """Ensure max batch size is reasonable."""
        if v <= 0:
            raise ValueError("max_batch_size must be positive")
        if v > 500:
            raise ValueError("max_batch_size should not exceed 500 for practical use")
        return v
    
    @field_validator("job_retention_hours")
    @classmethod
    def validate_job_retention_hours(cls, v: int) -> int:
        """Ensure job retention hours is reasonable."""
        if v < 1:
            raise ValueError("job_retention_hours must be at least 1 hour")
        if v > 168:  # 1 week
            raise ValueError("job_retention_hours should not exceed 168 (1 week)")
        return v
    
    @field_validator("job_cleanup_interval_seconds")
    @classmethod
    def validate_job_cleanup_interval(cls, v: int) -> int:
        """Ensure cleanup interval is reasonable."""
        if v < 60:  # Minimum 1 minute
            raise ValueError("job_cleanup_interval_seconds must be at least 60 seconds")
        if v > 86400:  # Maximum 1 day
            raise ValueError("job_cleanup_interval_seconds should not exceed 86400 (1 day)")
        return v
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Ensure log level is valid."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"log_level must be one of: {', '.join(valid_levels)}")
        return v.upper()
    
    def get_cors_origins(self) -> List[str]:
        """Parse CORS origins from JSON string."""
        try:
            origins = json.loads(self.cors_origins)
            if not isinstance(origins, list):
                return ["*"]
            return origins
        except json.JSONDecodeError:
            return ["*"]
    
    def get_allowed_hosts(self) -> List[str]:
        """Parse allowed hosts from JSON string and add domain_name if set."""
        try:
            hosts = json.loads(self.allowed_hosts)
            if not isinstance(hosts, list):
                hosts = ["localhost", "127.0.0.1", "testserver"]
        except json.JSONDecodeError:
            hosts = ["localhost", "127.0.0.1", "testserver"]
        
        # Add domain_name if configured
        if self.domain_name and self.domain_name not in hosts:
            hosts.append(self.domain_name)
        
        return hosts
    
    @property
    def max_file_size_bytes(self) -> int:
        """Get max file size in bytes."""
        return self.max_file_size_mb * 1024 * 1024


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Uses lru_cache to ensure settings are loaded only once
    and reused across the application.
    
    Returns:
        Settings instance with validated configuration
    """
    return Settings()
