from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings, extra="ignore"):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", env_ignore_env_file=True
    )

    GEMINI_API_KEY: str = Field(default="", json_schema_extra={"env": "GEMINI_API_KEY"})
    NOTION_API_KEY: str = Field(default="", json_schema_extra={"env": "NOTION_API_KEY"})
    NOTION_DATABASE_ID: str = Field(
        default="", json_schema_extra={"env": "NOTION_DATABASE_ID"}
    )
    GEMINI_MODEL: str = Field(
        default="gemini-2.0-flash", json_schema_extra={"env": "GEMINI_MODEL"}
    )
    TEMPERATURE: float = Field(default=0.0, json_schema_extra={"env": "TEMPERATURE"})
    TIMEZONE: str = Field(default="UTC", json_schema_extra={"env": "TIMEZONE"})
    MAX_GEMINI_CONCURRENT: int = Field(
        default=10, json_schema_extra={"env": "MAX_GEMINI_CONCURRENT"}
    )
    MAX_NOTION_CONCURRENT: int = Field(
        default=5, json_schema_extra={"env": "MAX_NOTION_CONCURRENT"}
    )


settings = Settings()
