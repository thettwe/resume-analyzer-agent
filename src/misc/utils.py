import csv
from typing import List
from rich.panel import Panel
from rich.text import Text

from ..api.models import Candidate


class CustomPanel(Panel):
    """Custom Panel class that includes the content in the string representation."""

    def __str__(self):
        """Custom string representation that includes the content."""
        if isinstance(self.renderable, Text):
            return str(self.renderable.plain)
        return str(self.renderable)


def format_processing_stats(
    total_files: int,
    processed_files: int,
    successful_files: int,
    duplicate_files: int,
    failed_files: int,
    notion_db_id: str,
) -> Panel:
    """
    Format the processing statistics for display.
    """
    summary = [
        "Processing Complete",
        f"{processed_files}/{total_files} files processed",
        f"{successful_files} uploaded to Notion",
        f"{duplicate_files} duplicates skipped",
        f"{failed_files} failed",
    ]

    if processed_files < total_files:
        summary.append(f"{total_files - processed_files} files were not processed")

    notion_url = f"https://notion.so/{notion_db_id.replace('-', '')}"
    summary.append(f"\nNotion Database URL: {notion_url}")

    summary_text = "\n".join(summary)
    return CustomPanel(summary_text, title="Processing Summary")


def write_candidates_to_csv(candidates: List[Candidate], file_path: str):
    """
    Writes a list of Candidate objects to a CSV file.
    """
    if not candidates:
        return

    header = list(Candidate.model_fields.keys())
    
    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for candidate in candidates:
            writer.writerow(
                [
                    getattr(candidate, field) for field in header
                ]
            )