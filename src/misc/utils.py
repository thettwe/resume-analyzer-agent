from rich.panel import Panel
from rich.text import Text


class CustomPanel(Panel):
    """Custom Panel class that includes the content in the string representation."""

    def __str__(self):
        """Custom string representation that includes the content."""
        # Handle either string or Text object as renderable
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

    Args:
        total_files: Total number of files found
        processed_files: Number of files processed
        successful_files: Number of files successfully uploaded to Notion
        duplicate_files: Number of files skipped as duplicates
        failed_files: Number of files that failed processing
        notion_db_id: Notion database ID

    Returns:
        Rich Panel containing the formatted summary
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

    # Add the Notion Database URL
    notion_url = f"https://notion.so/{notion_db_id.replace('-', '')}"
    summary.append(f"\nNotion Database URL: {notion_url}")

    summary_text = "\n".join(summary)
    return CustomPanel(summary_text, title="Processing Summary")
