
"""
Gemini API processing functionality for Resume Analyzer Agent
"""

import asyncio
from typing import Any, Dict, List, Optional

from google import genai
from rich import print as rprint
from rich.progress import Progress

from ..api.gemini import get_candidate_info


async def process_with_gemini(
    cv_data: List[Dict[str, Any]],
    jd_text: str,
    gemini_client: genai.Client,
    model: str,
    temperature: float,
    console,
    max_concurrent: int = 5,
    progress: Optional[Progress] = None,
    task_id=None,
) -> List[Dict[str, Any]]:
    """
    Process CV data with Gemini API.
    """
    processed_candidates = []
    failed_files = 0
    semaphore = asyncio.Semaphore(max_concurrent)

    async def process_cv_with_gemini(cv_item):
        async with semaphore:
            try:
                candidate = await get_candidate_info(
                    cv_text=cv_item["text"],
                    jd_text=jd_text,
                    client=gemini_client,
                    model=model,
                    temperature=temperature,
                )
                return {"status": "success", "file_name": cv_item["file_name"], "file_path": cv_item["file_path"], "candidate": candidate}
            except Exception as e:
                return {"status": "failed", "file_name": cv_item["file_name"], "error": str(e)}

    gemini_tasks = [process_cv_with_gemini(cv_item) for cv_item in cv_data]
    
    for future in asyncio.as_completed(gemini_tasks):
        result = await future
        if result["status"] == "success":
            processed_candidates.append(result)
        else:
            failed_files += 1
            rprint(f"\n[bold red]Error processing {result['file_name']} with Gemini: {result.get('error', 'Unknown error')}[/bold red]")
    
    if progress and task_id is not None:
        progress.update(task_id, advance=len(cv_data))

    return processed_candidates
