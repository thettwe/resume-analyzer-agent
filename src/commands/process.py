"""
Process command for Resume Analyzer Agent
"""

import os
from typing import Optional, List
import glob

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
    jobs_folder: str,
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
        jobs_folder: Path to the main jobs folder containing position sub-folders
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

    # Validate jobs_folder path
    if not os.path.isdir(jobs_folder):
        rprint(f"[bold red]Error:[/bold red] The specified path '{jobs_folder}' is not a valid directory or does not exist.")
        raise typer.Exit(code=1)

    # Initialize overall statistics
    overall_total_files = 0
    overall_processed_files = 0
    overall_successful_uploads = 0
    overall_duplicate_uploads = 0
    overall_failed_uploads = 0
    all_failed_files: List[str] = []
    all_duplicate_files: List[str] = []

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

    processed_log_file = ".processed_files.log"
    
    # Traverse the jobs folder
    for root, dirs, files in os.walk(jobs_folder):
        if "CVs" in dirs:
            cv_folder = os.path.join(root, "CVs")
            
            # Find JD file in the current root (position folder)
            jd_files_in_folder = [f for f in files if f.lower().endswith(".pdf")]

            jd_file = None
            if len(jd_files_in_folder) == 1:
                jd_file = os.path.join(root, jd_files_in_folder[0])
            elif len(jd_files_in_folder) > 1:
                rprint(
                    f"\n[bold yellow]Warning:[/bold yellow] Multiple PDF files found in '{root}'. Skipping this position as JD cannot be determined."
                )
                continue
            else:
                rprint(
                    f"\n[bold yellow]Warning:[/bold yellow] No PDF (JD) file found in '{root}'. Skipping this position."
                )
                continue

            rprint(
                Panel(
                    f"[bold blue]Processing Position:[/bold blue] {os.path.basename(root)}\n"
                    f"JD: {os.path.basename(jd_file)}\n"
                    f"CVs Folder: {os.path.basename(cv_folder)}",
                    title="Current Position",
                    expand=False,
                )
            )

            # Process JD file
            with console.status(f"[bold green]Processing Job Description: {os.path.basename(jd_file)}...[/bold green]"):
                try:
                    jd_text = extract_text_from_pdf(jd_file)
                    rprint(f"[bold green]✓[/bold green] Job Description '{os.path.basename(jd_file)}' processed")
                except Exception as e:
                    rprint(f"[bold red]Error processing Job Description '{os.path.basename(jd_file)}':[/bold red] {str(e)}")
                    continue # Skip to next position

            # Get CV files
            cv_files = get_cv_files(cv_folder)
            current_total_files = len(os.listdir(cv_folder))
            overall_total_files += current_total_files

            # Read processed files
            if os.path.exists(processed_log_file):
                with open(processed_log_file, "r") as f:
                    processed_files_set = set(f.read().splitlines())
            else:
                processed_files_set = set()

            # Filter out already processed files
            unprocessed_cv_files = [
                file for file in cv_files if os.path.basename(file) not in processed_files_set
            ]
            skipped_files_count = len(cv_files) - len(unprocessed_cv_files)

            if skipped_files_count > 0:
                rprint(
                    f"[bold yellow]Skipping {skipped_files_count} files that have already been processed for this position.[/bold yellow]"
                )

            if not unprocessed_cv_files:
                rprint(
                    f"[bold yellow]No new CV files to process for this position in {os.path.basename(cv_folder)}[/bold yellow]"
                )
                continue # Skip to next position

            current_processed_files = len(unprocessed_cv_files)
            overall_processed_files += current_processed_files

            # Format CV files for processing
            formatted_cv_files = format_cv_files(unprocessed_cv_files)

            # PHASE 1: Extract text from all CVs
            cv_data = await extract_cv_text(formatted_cv_files, console)

            if not cv_data:
                rprint(
                    "[bold yellow]No CV content could be extracted from any files for this position[/bold yellow]"
                )
                continue # Skip to next position

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
                    "[bold yellow]No candidates could be processed with Gemini API for this position[/bold yellow]"
                )
                continue # Skip to next position

            # PHASE 3: Upload to Notion
            (
                successful_files,
                duplicate_files,
                failed_files,
                successful_files_list,
                failed_files_list,
                duplicate_files_list,
            ) = await upload_to_notion(
                candidates=candidates,
                notion_manager=notion_manager,
                console=console,
                max_concurrent=max_notion_concurrent,
            )

            overall_successful_uploads += successful_files
            overall_duplicate_uploads += duplicate_files
            overall_failed_uploads += failed_files
            all_failed_files.extend(failed_files_list)
            all_duplicate_files.extend(duplicate_files_list)

            # Update processed files log
            if successful_files_list:
                with open(processed_log_file, "a") as f:
                    for file_name in successful_files_list:
                        f.write(f"{file_name}\n")

    # Display overall summary report
    rprint(Panel.fit("[bold green]Overall Processing Summary[/bold green]"))
    summary = format_processing_stats(
        total_files=overall_total_files,
        processed_files=overall_processed_files,
        successful_files=overall_successful_uploads,
        duplicate_files=overall_duplicate_uploads,
        failed_files=overall_failed_uploads,
        notion_db_id=config["NOTION_DATABASE_ID"],
    )
    rprint(summary)

    # Display all failed files
    if all_failed_files:
        rprint(Panel.fit("[bold red]All Failed Uploads[/bold red]"))
        for file_name in all_failed_files:
            rprint(f"- {file_name}")

    # Display all duplicate files
    if all_duplicate_files:
        rprint(Panel.fit("[bold yellow]All Duplicate Files (Skipped)[/bold yellow]"))
        for file_name in all_duplicate_files:
            rprint(f"- {file_name}")
