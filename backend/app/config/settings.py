from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Backend Configuration
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    # OSRM API Configuration
    osrm_base_url: str = "http://router.project-osrm.org"
    osrm_timeout_seconds: int = 30

    # OR-Tools Solver Configuration
    solver_time_limit_seconds: int = 30

    # CORS Configuration
    # Comma-separated list of allowed origins for cross-origin requests
    # Example: "http://localhost:3000,http://localhost:5173,https://yourdomain.com"
    # For development: Use localhost with your frontend port
    # For production: Use your actual domain(s) - NEVER use "*" in production
    allowed_origins: str = "http://localhost:3000,http://localhost:5173"

    # Logging Configuration
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    log_json_format: bool = False  # Use JSON structured logging
    log_file: str | None = None  # Optional log file path

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    @property
    def origins_list(self) -> list[str]:
        """Convert comma-separated origins string to list."""
        return [origin.strip() for origin in self.allowed_origins.split(",")]


# Global settings instance
settings = Settings()
