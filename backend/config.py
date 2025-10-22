from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    github_token: str | None = os.getenv("GITHUB_TOKEN")
    github_repo_url: str | None = os.getenv("GITHUB_REPO_URL")
    llm_endpoint: str = os.getenv("LLM_ENDPOINT", "http://localhost:11434/api/generate")
    llm_model: str = os.getenv("LLM_MODEL", "gpt-oss:20b")
    workspace_root: str = os.getenv("WORKSPACE_ROOT", "./workspaces")
    allow_run_cmd: bool = os.getenv("ALLOW_RUN_CMD", "true").lower() == "true"
    timezone: str = os.getenv("TIMEZONE", "Europe/Moscow")

settings = Settings()
