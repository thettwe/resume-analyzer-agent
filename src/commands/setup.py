"""
Setup command for Resume Analyzer Agent
"""

from rich import print as rprint
from rich.panel import Panel

from ..config.config import create_env_example


def setup_command():
    """
    Create a template .env.example file for configuration.
    """
    create_env_example()
    rprint(
        Panel(
            "[bold green]Setup completed![/bold green]\n\n"
            "A .env.example file has been created. Rename it to .env and fill in your API keys.",
            title="Resume Analyzer Agent - Setup",
            expand=False,
        )
    )
