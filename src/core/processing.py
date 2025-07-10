"""
Core processing logic for a single CV.
"""

import os
from typing import Any, Dict

from google import genai
from rich import print as rprint
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.console import Console

from ..api.notion import NotionManager
from ..misc.file_processor import extract_text_from_file


async def process_single_cv_quietly(
    cv_path: str,
    jd_text: str,
    config: Dict[str, Any],
    gemini_client: genai.Client,
    notion_manager: NotionManager,
    console: Console,
):
    """
    Processes a single CV file with a self-contained progress bar.
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}[/bold blue]"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(f"Processing {os.path.basename(cv_path)}", total=3)

        try:
            # 1. Extract text from the CV
            cv_text = extract_text_from_file(cv_path)
            progress.update(task, advance=1)
            if not cv_text.strip():
                rprint(f"[bold yellow]Warning:[/bold yellow] Empty text extracted from {os.path.basename(cv_path)}")
                return None, None, None
            
            # 2. Process with Gemini
            from ..api.gemini import get_candidate_info
            candidate = await get_candidate_info(
                cv_text=cv_text,
                jd_text=jd_text,
                client=gemini_client,
                model=config["GEMINI_MODEL"],
                temperature=float(config["TEMPERATURE"]),
            )
            progress.update(task, advance=1)

            # 3. Upload to Notion
            is_duplicate = await notion_manager.check_for_duplicate(
                email=candidate.email,
                position_title=candidate.job_position_title,
            )
            if is_duplicate:
                rprint(f"[bold yellow]Skipping duplicate candidate for this position (from watch): {candidate.full_name} ({candidate.email})[/bold yellow]")
                progress.update(task, advance=1)
                return None, None, [os.path.basename(cv_path)]

            page_id = await notion_manager.create_candidate_row(
                candidate=candidate,
                cv_filepath=cv_path,
            )
            progress.update(task, advance=1)
            
            if page_id:
                return [os.path.basename(cv_path)], [], []
            else:
                return [], [os.path.basename(cv_path)], []

        except Exception as e:
            rprint(f"[bold red]An error occurred while processing {os.path.basename(cv_path)}: {e}[/bold red]")
            return [], [os.path.basename(cv_path)], []