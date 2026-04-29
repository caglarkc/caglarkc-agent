from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = Field(default="ai-development-team-orchestrator", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_dir: Path = Field(default=Path("logs"), alias="LOG_DIR")
    log_file_name: str = Field(default="orchestrator.log", alias="LOG_FILE_NAME")
    log_max_bytes: int = Field(default=1_048_576, alias="LOG_MAX_BYTES")
    log_backup_count: int = Field(default=3, alias="LOG_BACKUP_COUNT")

    data_dir: Path = Field(default=Path("data"), alias="DATA_DIR")
    projects_root: Path = Field(default=Path("projects"), alias="PROJECTS_ROOT")
    sqlite_db_path: Path = Field(default=Path("data/orchestrator.db"), alias="SQLITE_DB_PATH")
    graph_checkpoint_path: Path = Field(
        default=Path("data/langgraph_checkpoints.sqlite"),
        alias="GRAPH_CHECKPOINT_PATH",
    )
    graph_thread_prefix: str = Field(default="phase1", alias="GRAPH_THREAD_PREFIX")
    http_timeout_seconds: float = Field(default=20.0, alias="HTTP_TIMEOUT_SECONDS")
    context_max_decisions: int = Field(default=5, alias="CONTEXT_MAX_DECISIONS")
    context_output_file: str = Field(default="context.md", alias="CONTEXT_OUTPUT_FILE")

    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    gemini_base_url: str = Field(
        default="https://generativelanguage.googleapis.com",
        alias="GEMINI_BASE_URL",
    )
    gemini_model: str = Field(default="gemini-2.0-flash", alias="GEMINI_MODEL")

    ollama_base_url: str = Field(default="http://127.0.0.1:11434", alias="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="qwen2.5:latest", alias="OLLAMA_MODEL")

    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        alias="OPENROUTER_BASE_URL",
    )
    openrouter_model: str = Field(default="openai/gpt-4.1-mini", alias="OPENROUTER_MODEL")
    openrouter_api_key_primary: str = Field(default="", alias="OPENROUTER_API_KEY_PRIMARY")
    openrouter_api_key_secondary: str = Field(default="", alias="OPENROUTER_API_KEY_SECONDARY")
    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str = Field(default="", alias="TELEGRAM_CHAT_ID")

    @property
    def log_file_path(self) -> Path:
        return self.log_dir / self.log_file_name

    @property
    def state_snapshot_path(self) -> Path:
        return self.data_dir / "state_snapshot.json"

    @property
    def daemon_pid_path(self) -> Path:
        return self.data_dir / "ai-orchestrator.pid"

    @property
    def daemon_status_path(self) -> Path:
        return self.data_dir / "daemon_status.json"

    @property
    def context_output_relative_path(self) -> Path:
        return Path(".meta") / self.context_output_file


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
