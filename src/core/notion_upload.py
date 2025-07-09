"""
Notion upload functionality for Resume Analyzer Agent
"""

import asyncio
from typing import Any, Dict, List, Tuple

from rich import print as rprint
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)

from api.notion import NotionManager


async def upload_to_notion(
    candidates: List[Dict[str, Any]],
    notion_manager: NotionManager,
    console,
    max_concurrent: int = 3,  # Maximum number of concurrent uploads
) -> Tuple[int, int, int, List[str], List[str]]:
    """
    Upload candidates to Notion database.

    Args:
        candidates: List of processed candidates
        notion_manager: Initialized NotionManager
        console: Rich console for display
        max_concurrent: Maximum number of concurrent uploads (default: 3)

    Returns:
        Tuple of (successful_files, duplicate_files, failed_files, failed_files_list, duplicate_files_list)
    """
    successful_files = 0
    duplicate_files = 0
    failed_files = 0
    failed_files_list = []
    duplicate_files_list = []

    # Create a semaphore to limit concurrent uploads
    semaphore = asyncio.Semaphore(max_concurrent)

    async def process_notion_upload(candidate_item):
        # Acquire the semaphore before processing
        async with semaphore:
            try:
                # Check for duplicate in Notion
                is_duplicate = await notion_manager.check_for_duplicate(
                    candidate_item["candidate"].email
                )

                if is_duplicate:
                    rprint(
                        f"\n[bold yellow]Skipping duplicate candidate: {candidate_item['candidate'].full_name} ({candidate_item['candidate'].email})[/bold yellow]"
                    )
                    return {
                        "status": "duplicate",
                        "file_name": candidate_item["file_name"],
                    }

                # Create Notion page
                page_id = await notion_manager.create_candidate_row(
                    candidate=candidate_item["candidate"],
                    cv_filepath=candidate_item["file_path"],
                )

                if page_id:
                    return {
                        "status": "success",
                        "file_name": candidate_item["file_name"],
                    }
                else:
                    return {
                        "status": "failed",
                        "file_name": candidate_item["file_name"],
                        "error": "Failed to create Notion page",
                    }

            except Exception as e:
                return {
                    "status": "failed",
                    "file_name": candidate_item["file_name"],
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
        notion_task = progress.add_task(
            f"Uploading {len(candidates)} candidates to Notion (max {max_concurrent} concurrent)...",
            total=len(candidates),
        )

        # Create and schedule all Notion tasks
        notion_tasks = [
            process_notion_upload(candidate_item) for candidate_item in candidates
        ]
        notion_results = []

        # Process tasks as they complete
        for future in asyncio.as_completed(notion_tasks):
            result = await future
            notion_results.append(result)

            if result["status"] == "success":
                successful_files += 1
            elif result["status"] == "duplicate":
                duplicate_files += 1
                duplicate_files_list.append(result["file_name"])
            else:
                failed_files += 1
                failed_files_list.append(result["file_name"])
                rprint(
                    f"\n[bold red]Error uploading {result['file_name']} to Notion: {result.get('error', 'Unknown error')}[/bold red]"
                )

            progress.update(notion_task, advance=1)

    return (
        successful_files,
        duplicate_files,
        failed_files,
        failed_files_list,
        duplicate_files_list,
    )

