"""
Resume Analyzer Agent: Main entry point
"""

import asyncio
from typing import Optional

import typer
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel

from commands.process import process_command

# Import command modules
from commands.setup import setup_command

# Create Typer app
app = typer.Typer(
    help="Resume Analyzer Agent streamlines the early stages of candidate screening by automatically analyzing resumes, matching them to job requirements, and posting the structured data to Notion."
)
console = Console()


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """
    Resume Analyzer Agent streamlines the early stages of candidate screening by automatically analyzing resumes, matching them to job requirements, and posting the structured data to Notion.
    """
    if ctx.invoked_subcommand is None:
        rprint(
            Panel(
                "[bold]Resume Analyzer Agent[/bold]\n\n"
                "This tool streamlines the early stages of candidate screening by automatically analyzing resumes, matching them to job requirements, and posting the structured data to Notion.\n\n"
                "[bold yellow]Available commands:[/bold yellow]\n"
                "  [bold]setup[/bold]    - Create a template .env file for configuration\n"
                "  [bold]process[/bold]  - Process CV files against a job description\n\n"
                "Run [bold]python src/app.py --help[/bold] for more information on available commands.",
                title="Resume Analyzer Agent",
                expand=False,
            )
        )


@app.command()
def setup():
    """
    Create a template .env.example file for configuration.
    """
    setup_command()


@app.command()
def process(
    jobs_folder: str = typer.Argument(
        ..., help="Path to the main jobs folder containing position sub-folders"
    ),
    notion_db_id: Optional[str] = typer.Option(
        None, "--notion-db", "-nd", help="Notion Database ID (overrides .env)"
    ),
    notion_api_key: Optional[str] = typer.Option(
        None, "--notion-api-key", "-na", help="Notion API Key (overrides .env)"
    ),
    gemini_api_key: Optional[str] = typer.Option(
        None, "--gemini-api-key", "-ga", help="Gemini API Key (overrides .env)"
    ),
    gemini_model: Optional[str] = typer.Option(
        None, "--gemini-model", "-gm", help="Gemini Model (overrides .env)"
    ),
    gemini_temperature: Optional[float] = typer.Option(
        None, "--gemini-temperature", "-gt", help="Gemini Temperature (overrides .env)"
    ),
    timezone: Optional[str] = typer.Option(
        None,
        "--timezone",
        "-tz",
        help="Timezone for date/time formatting (overrides .env)",
    ),
    max_gemini_concurrent: int = typer.Option(
        10,
        "--gemini-concurrency",
        "-gc",
        help="Maximum number of concurrent Gemini API calls",
    ),
    max_notion_concurrent: int = typer.Option(
        5,
        "--notion-concurrency",
        "-nc",
        help="Maximum number of concurrent Notion uploads",
    ),
):
    """
    Processes resumes for multiple job positions based on a structured folder layout.
    """
    # Run the process command asynchronously
    # try:
    asyncio.run(
        process_command(
            jobs_folder=jobs_folder,
            notion_db_id=notion_db_id,
            notion_api_key=notion_api_key,
            gemini_api_key=gemini_api_key,
            gemini_model=gemini_model,
            gemini_temperature=gemini_temperature,
            max_gemini_concurrent=max_gemini_concurrent,
            max_notion_concurrent=max_notion_concurrent,
            timezone=timezone,
            console=console,
        )
    )
