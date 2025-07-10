
"""
Text extraction functionality for Resume Analyzer Agent
"""

import os
from typing import Any, Dict, List, Optional

from rich import print as rprint
from rich.progress import Progress

from ..misc.file_processor import extract_text_from_file


async def extract_cv_text(
    cv_files: List[Dict[str, str]],
    console,
    progress: Optional[Progress] = None,
    task_id=None,
) -> List[Dict[str, Any]]:
    """
    Extract text from CV files.
    """
    cv_data = []
    for file in cv_files:
        try:
            cv_text = extract_text_from_file(file['file_path'])
            if cv_text.strip():
                cv_data.append(
                    {
                        "file_path": file['file_path'],
                        "file_name": file['file_name'],
                        "text": cv_text,
                    }
                )
            else:
                rprint(f"\n[bold yellow]Empty text extracted from {file['file_name']}[/bold yellow]")
        except Exception as e:
            rprint(f"\n[bold red]Error extracting text from {file['file_name']}: {str(e)}[/bold red]")

    if progress and task_id is not None:
        progress.update(task_id, advance=len(cv_files))
        
    return cv_data

