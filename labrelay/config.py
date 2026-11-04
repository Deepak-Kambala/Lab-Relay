from pathlib import Path
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Telegram Bot
    telegram_bot_token: str = Field(..., alias="TELEGRAM_BOT_TOKEN")
    telegram_bot_username: str = Field("deepak_labrelay_bot", alias="TELEGRAM_BOT_USERNAME")
    telegram_allowed_users: Optional[str] = Field(None, alias="TELEGRAM_ALLOWED_USERS")

    # Switch Core Integration
    switch_api_url: str = Field("http://127.0.0.1:63457", alias="SWITCH_API_URL")
    switch_db_host: str = Field("127.0.0.1", alias="SWITCH_DB_HOST")
    switch_db_port: int = Field(63459, alias="SWITCH_DB_PORT")
    switch_db_user: str = Field("switch_app", alias="SWITCH_DB_USER")
    switch_db_password: str = Field("", alias="SWITCH_DB_PASSWORD")
    switch_db_owner_user: str = Field("postgres", alias="SWITCH_DB_OWNER_USER")
    switch_db_owner_password: str = Field("", alias="SWITCH_DB_OWNER_PASSWORD")
    switch_db_name: str = Field("switch", alias="SWITCH_DB_NAME")
    switch_agent_registration_token: str = Field("", alias="SWITCH_AGENT_REGISTRATION_TOKEN")
    switch_gateway_admin_email: str = Field("admin@switch.local", alias="SWITCH_GATEWAY_ADMIN_EMAIL")
    switch_gateway_admin_password: str = Field("", alias="SWITCH_GATEWAY_ADMIN_PASSWORD")

    # Academic Literature APIs
    semantic_scholar_api_key: Optional[str] = Field(None, alias="SEMANTIC_SCHOLAR_API_KEY")

    # Paths
    workspace_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent)
    reports_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent / "reports")
    log_level: str = Field("INFO", alias="LOG_LEVEL")

    @property
    def allowed_users_list(self) -> List[str]:
        if not self.telegram_allowed_users:
            return []
        return [u.strip() for u in self.telegram_allowed_users.split(",") if u.strip()]

    def is_user_allowed(self, user_id: int, username: Optional[str] = None) -> bool:
        allowed = self.allowed_users_list
        if not allowed:
            return True  # If no restriction configured, allow
        if str(user_id) in allowed:
            return True
        if username and username.lstrip("@") in [u.lstrip("@") for u in allowed]:
            return True
        return False


settings = Settings()

