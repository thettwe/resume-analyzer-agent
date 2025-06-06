from typing import Dict, Optional

from rich import print as rprint

from config.settings import settings


def get_config(
    cli_notion_db_id: Optional[str] = None,
    cli_notion_api_key: Optional[str] = None,
    cli_gemini_api_key: Optional[str] = None,
    cli_gemini_model: Optional[str] = None,
    cli_temperature: Optional[float] = None,
    cli_timezone: Optional[str] = None,
) -> Dict[str, str]:
    """
    Load configuration from .env file with CLI overrides.

    Args:
        cli_notion_db_id: Optional Notion Database ID from CLI arguments
        cli_notion_api_key: Optional Notion API key from CLI arguments
        cli_gemini_api_key: Optional Gemini API key from CLI arguments
        cli_gemini_model: Optional Gemini model name from CLI arguments
        cli_temperature: Optional temperature value from CLI arguments
        cli_timezone: Optional timezone value from CLI arguments

    Returns:
        Dictionary with configuration values

    Raises:
        ValueError: If required configuration is missing
    """

    # Get configuration values with CLI overrides
    config = {
        "GEMINI_API_KEY": cli_gemini_api_key or settings.GEMINI_API_KEY,
        "NOTION_API_KEY": cli_notion_api_key or settings.NOTION_API_KEY,
        "NOTION_DATABASE_ID": cli_notion_db_id or settings.NOTION_DATABASE_ID,
        "GEMINI_MODEL": cli_gemini_model or settings.GEMINI_MODEL,
        "TEMPERATURE": cli_temperature or settings.TEMPERATURE,
        "TIMEZONE": cli_timezone or settings.TIMEZONE,
    }

    # Check for required configuration
    required_keys = ["GEMINI_API_KEY", "NOTION_API_KEY", "NOTION_DATABASE_ID"]
    missing = [k for k in required_keys if not config[k]]

    if missing:
        missing_str = ", ".join(missing)
        error_msg = (
            f"Missing required configuration: {missing_str}. "
            f"Please add these to your .env file or provide them as CLI arguments."
        )
        raise ValueError(error_msg)

    return config


def create_env_example() -> None:
    """
    Create a .env.example file with required configuration variables.
    """
    env_example_content = """# Google Gemini API key
GEMINI_API_KEY=your_gemini_api_key_here

# Notion API key
NOTION_API_KEY=your_notion_api_key_here

# Notion database ID
NOTION_DATABASE_ID=your_notion_database_id_here

# Optional: Gemini model name (default: gemini-2.0-flash)
GEMINI_MODEL=gemini-2.0-flash

# Optional: Temperature for Gemini API (default: 0.0)
TEMPERATURE=0.0

# Optional: Timezone for date/time formatting (default: UTC)
TIMEZONE=UTC
    """

    with open(".env.example", "w") as f:
        f.write(env_example_content)

    rprint("[bold green]Created .env.example file successfully.[/bold green]")
