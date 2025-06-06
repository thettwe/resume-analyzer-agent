"""
Gemini API processing functionality for Resume Analyzer Agent
"""

import asyncio
from typing import Any, Dict, List

from google import genai
from rich import print as rprint
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)

from api.gemini import get_candidate_info


async def process_with_gemini(
    cv_data: List[Dict[str, Any]],
    jd_text: str,
    gemini_client: genai.Client,
    model: str,
    temperature: float,
    console,
    max_concurrent: int = 5,  # Maximum number of concurrent API calls
) -> List[Dict[str, Any]]:
    """
    Process CV data with Gemini API.

    Args:
        cv_data: List of dictionaries with file info and extracted text
        jd_text: Job description text
        gemini_client: Initialized Gemini client
        model: Gemini model name
        temperature: Generation temperature
        console: Rich console for display
        max_concurrent: Maximum number of concurrent API calls (default: 5)

    Returns:
        List of successfully processed candidates
    """
    processed_candidates = []
    failed_files = 0

    # Create a semaphore to limit concurrent processing
    semaphore = asyncio.Semaphore(max_concurrent)

    async def process_cv_with_gemini(cv_item):
        # Acquire the semaphore before processing
        async with semaphore:
            try:
                # Process with Gemini
                candidate = await get_candidate_info(
                    cv_text=cv_item["text"],
                    jd_text=jd_text,
                    client=gemini_client,
                    model=model,
                    temperature=temperature,
                )
                return {
                    "status": "success",
                    "file_name": cv_item["file_name"],
                    "file_path": cv_item["file_path"],
                    "candidate": candidate,
                }
            except Exception as e:
                return {
                    "status": "failed",
                    "file_name": cv_item["file_name"],
                    "error": str(e),
                }

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}[/bold blue]"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        gemini_task = progress.add_task(
            f"Processing {len(cv_data)} CVs with Gemini API (max {max_concurrent} concurrent)...",
            total=len(cv_data),
        )

        # Create and schedule all Gemini tasks
        gemini_tasks = [process_cv_with_gemini(cv_item) for cv_item in cv_data]
        gemini_results = []

        # Process tasks as they complete
        for future in asyncio.as_completed(gemini_tasks):
            result = await future
            gemini_results.append(result)

            if result["status"] == "success":
                processed_candidates.append(result)
            else:
                failed_files += 1
                rprint(
                    f"\n[bold red]Error processing {result['file_name']} with Gemini: {result.get('error', 'Unknown error')}[/bold red]"
                )

            progress.update(gemini_task, advance=1)

    rprint(
        f"[bold green]✓[/bold green] Processed {len(processed_candidates)} CVs with Gemini API"
    )

    if failed_files > 0:
        rprint(
            f"\n[bold yellow]⚠[/bold yellow] Failed to process {failed_files} files with Gemini API"
        )

    return processed_candidates
