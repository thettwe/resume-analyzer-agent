
"""
Helper functions for CLI commands.
"""
from typing import Dict, Any, Optional
import pytz
import typer
from google import genai
from rich import print as rprint

from ..api.gemini import verify_gemini_api_key
from ..api.notion import NotionManager
from ..config.config import get_config


async def initialize_clients(
    notion_db_id: Optional[str],
    notion_api_key: Optional[str],
    gemini_api_key: Optional[str],
    gemini_model: Optional[str],
    gemini_temperature: Optional[float],
    timezone: Optional[str],
) -> Dict[str, Any]:
    """
    Loads configuration and initializes API clients.
    """
    try:
        config = get_config(
            notion_db_id,
            notion_api_key,
            gemini_api_key,
            gemini_model,
            gemini_temperature,
            timezone,
        )
    except ValueError as e:
        rprint(f"[bold red]Configuration Error:[/bold red] {str(e)}")
        rprint("\nRun [bold]python src/app.py setup[/bold] to create a template .env file.")
        raise typer.Exit(code=1)

    try:
        pytz.timezone(config["TIMEZONE"])
    except pytz.exceptions.UnknownTimeZoneError:
        rprint(f"[bold red]Invalid timezone:[/bold red] {config['TIMEZONE']}")
        raise typer.Exit(code=1)

    try:
        await verify_gemini_api_key(config["GEMINI_API_KEY"])
        gemini_client = genai.Client(api_key=config["GEMINI_API_KEY"])
    except Exception as e:
        rprint(f"[bold red]Error initializing Gemini client:[/bold red] {str(e)}")
        raise typer.Exit(code=1)

    try:
        notion_manager = await NotionManager(
            token=config["NOTION_API_KEY"],
            database_id=config["NOTION_DATABASE_ID"],
            timezone=config["TIMEZONE"],
        ).configure()
    except Exception as e:
        rprint(f"[bold red]Error initializing Notion client:[/bold red] {str(e)}")
        raise typer.Exit(code=1)

    return {
        "config": config,
        "gemini_client": gemini_client,
        "notion_manager": notion_manager,
    }

