"""Environment-driven application settings."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Validated runtime settings loaded from ``backend/.env`` and the environment."""

    model_config = SettingsConfigDict(
        env_file=BACKEND_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "CarVerse Drive API"
    environment: Literal["development", "test", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    database_url: str = "sqlite+aiosqlite:///./data/carverse.db"
    data_directory: Path = Path("./data")
    ingest_batch_size: int = Field(default=2000, ge=100, le=10_000)
    scoring_batch_size: int = Field(default=2000, ge=100, le=10_000)
    sql_echo: bool = False
    auto_reseed_on_startup: bool = True

    rework_discount_percent: int = Field(default=15, ge=0, le=100)
    cross_dept_assist_business_hours: int = Field(default=4, gt=0, le=24)
    escalation_resolution_hours: int = Field(default=24, gt=0, le=168)
    fast_delivery_max_days: int = Field(default=180, gt=0)
    business_day_start_hour: int = Field(default=9, ge=0, le=23)
    business_day_end_hour: int = Field(default=18, ge=1, le=24)
    business_working_days: str = "0,1,2,3,4,5"
    max_cross_dept_assists_per_booking: int = Field(default=6, ge=0, le=12)
    daily_leaderboard_xp_cap: int = Field(default=500, gt=0)
    weekly_leaderboard_xp_cap: int = Field(default=2500, gt=0)
    daily_delivery_leaderboard_cap: int = Field(default=5, gt=0)
    level_xp_base: int = Field(default=100, gt=0)
    level_xp_exponent: float = Field(default=1.5, gt=1)
    reputation_clean_weight: int = Field(default=40, ge=0, le=100)
    reputation_recovery_weight: int = Field(default=25, ge=0, le=100)
    reputation_quality_weight: int = Field(default=35, ge=0, le=100)
    streak_milestone_bonuses: str = "3:10,7:25,14:60,30:150"

    jwt_secret: SecretStr = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = Field(default=1440, gt=0)
    jwt_issuer: str = "carverse-drive"
    jwt_audience: str = "carverse-frontend"

    mistral_api_key: SecretStr | None = None
    mistral_model: str = "mistral-small-latest"
    gemini_api_key: SecretStr | None = None
    gemini_model: str = "gemini-2.0-flash"
    ai_cache_ttl_seconds: int = Field(default=3600, ge=0)
    ai_timeout_seconds: float = Field(default=12, gt=0, le=60)
    anomaly_z_threshold: float = Field(default=2.5, gt=0, le=10)
    scheduler_enabled: bool = True
    scheduler_timezone: str = "Asia/Kolkata"
    scheduler_nightly_hour: int = Field(default=2, ge=0, le=23)
    scheduler_nightly_minute: int = Field(default=15, ge=0, le=59)
    scheduler_weekly_day: str = "mon"

    cors_allowed_origins: str = "http://localhost:3000,http://localhost:5173"
    active_departments: str = "SALES,FINANCE,ACCOUNTS,CUSTOMER CARE,PDI"

    @field_validator("mistral_api_key", "gemini_api_key", mode="before")
    @classmethod
    def empty_secret_is_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @property
    def cors_origins(self) -> list[str]:
        """Return the configured, de-duplicated frontend origins."""

        return list(
            dict.fromkeys(
                origin.strip().rstrip("/")
                for origin in self.cors_allowed_origins.split(",")
                if origin.strip()
            )
        )

    @property
    def active_department_names(self) -> tuple[str, ...]:
        """Return canonical active department names in configured order."""

        return tuple(
            dict.fromkeys(
                department.strip().upper()
                for department in self.active_departments.split(",")
                if department.strip()
            )
        )

    @property
    def resolved_data_directory(self) -> Path:
        """Resolve relative data paths from the backend root, not the caller's cwd."""

        if self.data_directory.is_absolute():
            return self.data_directory
        return (BACKEND_ROOT / self.data_directory).resolve()

    @property
    def working_weekdays(self) -> frozenset[int]:
        days = frozenset(
            int(day.strip())
            for day in self.business_working_days.split(",")
            if day.strip()
        )
        if not days or any(day < 0 or day > 6 for day in days):
            raise ValueError("BUSINESS_WORKING_DAYS must contain values from 0 to 6")
        return days

    @property
    def streak_bonuses(self) -> dict[int, int]:
        bonuses: dict[int, int] = {}
        for item in self.streak_milestone_bonuses.split(","):
            threshold, points = item.split(":", 1)
            bonuses[int(threshold.strip())] = int(points.strip())
        if not bonuses or any(threshold <= 0 or points <= 0 for threshold, points in bonuses.items()):
            raise ValueError("STREAK_MILESTONE_BONUSES must contain positive threshold:points pairs")
        return dict(sorted(bonuses.items()))


@lru_cache
def get_settings() -> Settings:
    """Return one immutable-by-convention settings instance per process."""

    return Settings()  # type: ignore[call-arg]


settings = get_settings()
