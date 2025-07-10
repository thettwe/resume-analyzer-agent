"""
Process command for Resume Analyzer Agent
"""

import os
from typing import Any, Dict, Optional, List
import asyncio

import typer
from google import genai
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from .helpers import initialize_clients
from ..api.gemini import get_candidate_info
from ..misc.file_processor import extract_text_from_pdf, get_cv_files, extract_text_from_file
from ..misc.utils import format_processing_stats, write_candidates_to_csv


async def run_batch_processing(
    jobs_folder: str,
    config: Dict[str, Any],
    gemini_client: genai.Client,
    notion_manager: Any,
    console: Console,
    max_gemini_concurrent: int,
    max_notion_concurrent: int,
    output_csv_path: Optional[str] = None,
):
    """
    Scans the jobs folder and processes all unprocessed CVs.
    """
    overall_total_files = 0
    overall_processed_files = 0
    overall_successful_uploads = 0
    overall_duplicate_uploads = 0
    overall_failed_uploads = 0
    all_failed_files: List[str] = []
    all_duplicate_files: List[str] = []
    all_successful_candidates = []
    
    job_folders = [os.path.join(jobs_folder, d) for d in os.listdir(jobs_folder) if os.path.isdir(os.path.join(jobs_folder, d))]

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}[/bold blue]"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        for root in job_folders:
            if "CVs" in os.listdir(root):
                cv_folder = os.path.join(root, "CVs")
                jd_files_in_folder = [f for f in os.listdir(root) if f.lower().endswith(".pdf")]

                if len(jd_files_in_folder) != 1:
                    rprint(f"\n[bold yellow]Warning:[/bold yellow] Skipping '{root}' due to missing or multiple JD files.")
                    continue

                cv_files = get_cv_files(cv_folder)
                overall_total_files += len(cv_files)

                processed_log_file = os.path.join(root, ".processed_files.log")
                if os.path.exists(processed_log_file):
                    with open(processed_log_file, "r") as f:
                        processed_files_set = set(f.read().splitlines())
                else:
                    processed_files_set = set()

                unprocessed_cv_files = [file for file in cv_files if os.path.basename(file) not in processed_files_set]
                if not unprocessed_cv_files:
                    continue
                
                position_task = progress.add_task(f"Processing {os.path.basename(root)}", total=len(unprocessed_cv_files))
                
                jd_file = os.path.join(root, jd_files_in_folder[0])
                try:
                    jd_text = extract_text_from_pdf(jd_file)
                except Exception as e:
                    rprint(f"[bold red]Error processing Job Description '{os.path.basename(jd_file)}':[/bold red] {str(e)}")
                    continue

                for cv_path in unprocessed_cv_files:
                    try:
                        cv_text = extract_text_from_file(cv_path)
                        if not cv_text.strip():
                            rprint(f"[bold yellow]Warning:[/bold yellow] Empty text extracted from {os.path.basename(cv_path)}")
                            continue

                        candidate = await get_candidate_info(
                            cv_text=cv_text,
                            jd_text=jd_text,
                            client=gemini_client,
                            model=config["GEMINI_MODEL"],
                            temperature=float(config["TEMPERATURE"]),
                        )

                        is_duplicate = await notion_manager.check_for_duplicate(
                            email=candidate.email,
                            position_title=candidate.job_position_title,
                        )

                        if is_duplicate:
                            rprint(f"[bold yellow]Skipping duplicate candidate for this position: {candidate.full_name} ({candidate.email})[/bold yellow]")
                            overall_duplicate_uploads += 1
                            all_duplicate_files.append(os.path.basename(cv_path))
                            continue

                        page_id = await notion_manager.create_candidate_row(
                            candidate=candidate,
                            cv_filepath=cv_path,
                        )

                        if page_id:
                            overall_successful_uploads += 1
                            all_successful_candidates.append(candidate)
                            with open(processed_log_file, "a") as f:
                                f.write(f"{os.path.basename(cv_path)}\n")
                        else:
                            overall_failed_uploads += 1
                            all_failed_files.append(os.path.basename(cv_path))

                    except Exception as e:
                        rprint(f"[bold red]An error occurred while processing {os.path.basename(cv_path)}: {e}[/bold red]")
                        overall_failed_uploads += 1
                        all_failed_files.append(os.path.basename(cv_path))
                    finally:
                        progress.update(position_task, advance=1)
                
                overall_processed_files += len(unprocessed_cv_files)

    if output_csv_path and all_successful_candidates:
        write_candidates_to_csv(all_successful_candidates, output_csv_path)
        rprint(f"\n[bold green]✓[/bold green] Successfully saved report to [bold]{output_csv_path}[/bold]")

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

    if all_failed_files:
        rprint(Panel.fit("[bold red]All Failed Uploads[/bold red]"))
        for file_name in all_failed_files:
            rprint(f"- {file_name}")

    if all_duplicate_files:
        rprint(Panel.fit("[bold yellow]All Duplicate Files (Skipped)[/bold yellow]"))
        for file_name in all_duplicate_files:
            rprint(f"- {file_name}")


async def process_command(
    jobs_folder: str,
    notion_db_id: Optional[str],
    notion_api_key: Optional[str],
    gemini_api_key: Optional[str],
    gemini_model: Optional[str],
    gemini_temperature: Optional[float],
    max_gemini_concurrent: Optional[int],
    max_notion_concurrent: Optional[int],
    timezone: Optional[str],
    console: Console,
    output_csv_path: Optional[str],
):
    """
    Processes the candidate screening by automatically analyzing resumes, matching them to job requirements, and posting the structured data to Notion.
    """
    rprint(
        Panel(
            "[bold]Resume Analyzer Agent[/bold]\n\n"
            "This tool streamlines the early stages of candidate screening by automatically analyzing resumes, matching them to job requirements, and posting the structured data to Notion.",
            title="Welcome",
            expand=False,
        )
    )

    if not os.path.isdir(jobs_folder):
        rprint(f"[bold red]Error:[/bold red] The specified path '{jobs_folder}' is not a valid directory or does not exist.")
        raise typer.Exit(code=1)

    clients = await initialize_clients(
        notion_db_id,
        notion_api_key,
        gemini_api_key,
        gemini_model,
        gemini_temperature,
        timezone,
    )

    await run_batch_processing(
        jobs_folder=jobs_folder,
        config=clients["config"],
        gemini_client=clients["gemini_client"],
        notion_manager=clients["notion_manager"],
        console=console,
        max_gemini_concurrent=max_gemini_concurrent,
        max_notion_concurrent=max_notion_concurrent,
        output_csv_path=output_csv_path,
    )