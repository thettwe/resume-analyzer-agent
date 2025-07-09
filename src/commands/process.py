"""
Process command for Resume Analyzer Agent
"""

import os
from typing import Optional

import pytz
import typer
from google import genai
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel

from api.gemini import verify_gemini_api_key
from api.notion import NotionManager
from config.config import get_config
from core.extraction import extract_cv_text
from core.gemini_processing import process_with_gemini
from core.notion_upload import upload_to_notion
from misc.file_processor import extract_text_from_pdf, format_cv_files, get_cv_files
from misc.utils import format_processing_stats


async def process_command(
    cv_folder: str,
    jd_file: str,
    notion_db_id: Optional[str],
    notion_api_key: Optional[str],
    gemini_api_key: Optional[str],
    gemini_model: Optional[str],
    gemini_temperature: Optional[float],
    max_gemini_concurrent: Optional[int] = 5,
    max_notion_concurrent: Optional[int] = 3,
    timezone: Optional[str] = None,
    console: Console = Console(),
):
    """
    Processes the candidate screening by automatically analyzing resumes, matching them to job requirements, and posting the structured data to Notion.

    Args:
        cv_folder: Path to folder containing CV files
        jd_file: Path to Job Description PDF file
        notion_db_id: Notion Database ID (overrides .env)
        notion_api_key: Notion API Key (overrides .env)
        gemini_api_key: Gemini API Key (overrides .env)
        gemini_model: Gemini Model (overrides .env)
        gemini_temperature: Gemini Temperature (overrides .env)
        max_gemini_concurrent: Maximum number of concurrent Gemini API calls (default: 5)
        max_notion_concurrent: Maximum number of concurrent Notion uploads (default: 3)
        timezone: Timezone for date/time formatting (overrides .env)
        console: Rich console for display

    Raises:
        typer.Exit: To exit the CLI application
    """
    # Display welcome message
    rprint(
        Panel(
            "[bold]Resume Analyzer Agent[/bold]\n\n"
            "This tool streamlines the early stages of candidate screening by automatically analyzing resumes, matching them to job requirements, and posting the structured data to Notion.",
            title="Welcome",
            expand=False,
        )
    )

    # Run the main processing
    """
    Main processing function that coordinates the CV scanning workflow.

    Args:
        cv_folder: Path to folder containing CV files
        jd_file: Path to JD PDF file
        notion_db_id: Notion database ID (optional, from CLI)
        notion_api_key: Notion API key (optional, from CLI)
        gemini_api_key: Gemini API key (optional, from CLI)
        gemini_model: Gemini model name (optional, from CLI)
        gemini_temperature: Gemini temperature (optional, from CLI)
        timezone: Timezone for date formatting (optional, from CLI)
        console: Rich console for display

    Raises:
        ValueError: If required files are not found
        typer.Exit: To exit the CLI application
    """
    # Pre-run checks
    if not os.path.exists(cv_folder):
        raise ValueError(f"CV folder not found: {cv_folder}")
    if not os.path.exists(jd_file):
        raise ValueError(f"Job Description file not found: {jd_file}")
    if not jd_file.lower().endswith(".pdf"):
        raise ValueError(f"Job Description must be a PDF file: {jd_file}")

    # Load configuration
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
        rprint(
            "\nRun [bold]python src/app.py setup[/bold] to create a template .env file."
        )
        raise typer.Exit(code=1)

    # Verify timezone
    try:
        pytz.timezone(config["TIMEZONE"])
    except pytz.exceptions.UnknownTimeZoneError:
        rprint(f"[bold red]Invalid timezone:[/bold red] {config['TIMEZONE']}")
        raise typer.Exit(code=1)
    
    
    # Initialize clients
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

    if not notion_manager:
        rprint(
            "[bold red]Error:[/bold red] Failed to configure Notion client. Please check your API key and database ID."
        )
        raise typer.Exit(code=1)

    # Process JD file
    with console.status("[bold green]Processing Job Description...[/bold green]"):
        try:
            jd_text = extract_text_from_pdf(jd_file)
            rprint("[bold green]✓[/bold green] Job Description file processed")
        except Exception as e:
            rprint(f"[bold red]Error processing Job Description:[/bold red] {str(e)}")
            raise typer.Exit(code=1)

    # Get CV files
    cv_files = get_cv_files(cv_folder)
    total_files = len(os.listdir(cv_folder))
    processed_files = len(cv_files)

    if not cv_files:
        rprint(
            f"[bold yellow]No supported CV files (PDF, DOCX) found in {cv_folder}[/bold yellow]"
        )
        raise typer.Exit(code=0)

    # Format CV files for processing
    formatted_cv_files = format_cv_files(cv_files)

    # PHASE 1: Extract text from all CVs
    cv_data = await extract_cv_text(formatted_cv_files, console)

    if not cv_data:
        rprint(
            "[bold yellow]No CV content could be extracted from any files[/bold yellow]"
        )
        raise typer.Exit(code=0)

    # PHASE 2: Process with Gemini API
    candidates = await process_with_gemini(
        cv_data=cv_data,
        jd_text=jd_text,
        gemini_client=gemini_client,
        model=config["GEMINI_MODEL"],
        temperature=float(config["TEMPERATURE"]),
        console=console,
        max_concurrent=max_gemini_concurrent,
    )

    if not candidates:
        rprint(
            "[bold yellow]No candidates could be processed with Gemini API[/bold yellow]"
        )
        raise typer.Exit(code=0)

    # PHASE 3: Upload to Notion
    (
        successful_files,
        duplicate_files,
        failed_files,
        failed_files_list,
        duplicate_files_list,
    ) = await upload_to_notion(
        candidates=candidates,
        notion_manager=notion_manager,
        console=console,
        max_concurrent=max_notion_concurrent,
    )

    # Display summary report
    summary = format_processing_stats(
        total_files=total_files,
        processed_files=processed_files,
        successful_files=successful_files,
        duplicate_files=duplicate_files,
        failed_files=failed_files + (processed_files - len(candidates)),
        notion_db_id=config["NOTION_DATABASE_ID"],
    )

    rprint(summary)

    # Display failed files, if any
    if failed_files_list:
        rprint(Panel.fit("[bold red]Failed Uploads[/bold red]"))
        for file_name in failed_files_list:
            rprint(f"- {file_name}")

    # Display duplicate files, if any
    if duplicate_files_list:
        rprint(Panel.fit("[bold yellow]Duplicate Files (Skipped)[/bold yellow]"))
        for file_name in duplicate_files_list:
            rprint(f"- {file_name}")
