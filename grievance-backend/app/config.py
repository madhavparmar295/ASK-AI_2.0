from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "development"  # development | test | production
    database_url: str = "postgresql+psycopg://grievance:grievance@localhost:5432/grievance"
    secret_key: str = "change-me"
    google_client_id: str = ""
    allowed_email_domain: str = "college.edu"
    require_hd: bool = True
    session_ttl_hours: int = 12
    cookie_secure: bool = False
    dev_login_enabled: bool = True
    unknown_email_policy: str = "reject"  # reject | student
    api_prefix: str = "/api/grievance"
    cors_origins: str = "http://localhost:5173"
    login_rate_limit_per_minute: int = 10

    @property
    def is_production(self) -> bool:
        return self.env.lower() == "production"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def validate_for_runtime(self) -> None:
        """Refuse to start in production with unsafe settings."""
        if self.unknown_email_policy not in ("reject", "student"):
            raise RuntimeError("UNKNOWN_EMAIL_POLICY must be 'reject' or 'student'")
        if not self.is_production:
            return
        problems = []
        if self.dev_login_enabled:
            problems.append("DEV_LOGIN_ENABLED must be false")
        if self.secret_key == "change-me" or len(self.secret_key) < 32:
            problems.append("SECRET_KEY must be a random string of 32+ characters")
        if not self.cookie_secure:
            problems.append("COOKIE_SECURE must be true (HTTPS)")
        if not self.google_client_id:
            problems.append("GOOGLE_CLIENT_ID must be set")
        if problems:
            raise RuntimeError("Unsafe production configuration: " + "; ".join(problems))


@lru_cache
def get_settings() -> Settings:
    return Settings()
