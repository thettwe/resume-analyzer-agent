"""
Notion upload functionality for Resume Analyzer Agent
"""

import asyncio
from typing import Any, Dict, List, Tuple, Optional

from rich import print as rprint
from rich.progress import Progress

from ..api.notion import NotionManager


async def upload_to_notion(
    candidates: List[Dict[str, Any]],
    notion_manager: NotionManager,
    console,
    max_concurrent: int = 3,
    progress: Optional[Progress] = None,
    task_id=None,
) -> Tuple[int, int, int, List[str], List[str], List[str]]:
    """
    Upload candidates to Notion database.
    """
    successful_files = 0
    duplicate_files = 0
    failed_files = 0
    successful_files_list = []
    failed_files_list = []
    duplicate_files_list = []
    semaphore = asyncio.Semaphore(max_concurrent)

    async def process_notion_upload(candidate_item):
        async with semaphore:
            try:
                is_duplicate = await notion_manager.check_for_duplicate(
                    email=candidate_item["candidate"].email,
                    position_title=candidate_item["candidate"].job_position_title,
                )
                if is_duplicate:
                    rprint(f"\n[bold yellow]Skipping duplicate candidate for this position: {candidate_item['candidate'].full_name} ({candidate_item['candidate'].email})[/bold yellow]")
                    return {"status": "duplicate", "file_name": candidate_item["file_name"]}
                
                page_id = await notion_manager.create_candidate_row(candidate=candidate_item["candidate"], cv_filepath=candidate_item["file_path"])
                if page_id:
                    return {"status": "success", "file_name": candidate_item["file_name"]}
                else:
                    return {"status": "failed", "file_name": candidate_item["file_name"], "error": "Failed to create Notion page"}
            except Exception as e:
                return {"status": "failed", "file_name": candidate_item["file_name"], "error": str(e)}

    upload_tasks = [process_notion_upload(candidate_item) for candidate_item in candidates]

    for future in asyncio.as_completed(upload_tasks):
        result = await future
        if result["status"] == "success":
            successful_files += 1
            successful_files_list.append(result["file_name"])
        elif result["status"] == "duplicate":
            duplicate_files += 1
            duplicate_files_list.append(result["file_name"])
        else:
            failed_files += 1
            failed_files_list.append(result["file_name"])
            rprint(f"\n[bold red]Error uploading {result['file_name']} to Notion: {result.get('error', 'Unknown error')}[/bold red]")
    
    if progress and task_id is not None:
        progress.update(task_id, advance=len(candidates))

    return successful_files, duplicate_files, failed_files, successful_files_list, failed_files_list, duplicate_files_list