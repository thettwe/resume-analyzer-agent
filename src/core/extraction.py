"""
Text extraction functionality for Resume Analyzer Agent
"""

import os
from typing import Any, Dict, List

from rich import print as rprint
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)

from misc.file_processor import extract_text_from_file


async def extract_cv_text(cv_files: List[Dict[str, str]], console) -> List[Dict[str, Any]]:
    """
    Extract text from CV files.

    Args:
        cv_files: List of CV file paths
        console: Rich console for display

    Returns:
        List of dictionaries with file info and extracted text
    """
    cv_data = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}[/bold blue]"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        extract_task = progress.add_task(
            f"Extracting text from {len(cv_files)} CV files...", total=len(cv_files)
        )

        for idx, file in enumerate(cv_files, 1):
            progress.update(
                extract_task,
                description=f"Extracting CV {idx} of {len(cv_files)}: {file['file_name']}",
            )

            try:
                # Extract text from CV
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
                    rprint(
                        f"\n[bold yellow]Empty text extracted from {file['file_name']}[/bold yellow]"
                    )
            except Exception as e:
                rprint(
                    f"\n[bold red]Error extracting text from {file['file_name']}: {str(e)}[/bold red]"
                )

            progress.update(extract_task, advance=1)

    rprint(f"[bold green]✓[/bold green] Extracted text from {len(cv_data)} CV files")
    return cv_data
