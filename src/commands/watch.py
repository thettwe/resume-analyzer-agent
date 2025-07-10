
"""
Watch command for Resume Analyzer Agent.
"""

import asyncio
import os
import time
from typing import Any, Dict, Optional, Set

import typer
from rich.console import Console
from rich.panel import Panel
from rich import print as rprint
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .helpers import initialize_clients
from ..core.processing import process_single_cv_quietly
from ..misc.file_processor import extract_text_from_pdf
from .process import run_batch_processing


class CVEventHandler(FileSystemEventHandler):
    def __init__(
        self,
        config: Dict[str, Any],
        clients: Dict[str, Any],
        loop: asyncio.AbstractEventLoop,
        jobs_folder: str,
        console: Console,
    ):
        self.config = config
        self.gemini_client = clients["gemini_client"]
        self.notion_manager = clients["notion_manager"]
        self.loop = loop
        self.jobs_folder = jobs_folder
        self.console = console
        self.processed_files = set()

    def on_created(self, event):
        if event.is_directory or not event.src_path.lower().endswith((".pdf", ".docx")):
            return

        time.sleep(2)
        
        cv_path = event.src_path
        cv_filename = os.path.basename(cv_path)
        position_folder = os.path.dirname(os.path.dirname(cv_path))
        processed_log_file = os.path.join(position_folder, ".processed_files.log")

        if cv_filename in self.processed_files:
            return

        # Re-read the log file each time to get the most up-to-date list
        if os.path.exists(processed_log_file):
            with open(processed_log_file, "r") as f:
                self.processed_files = set(f.read().splitlines())

        if cv_filename in self.processed_files:
            return

        cv_folder = os.path.dirname(cv_path)
        if os.path.basename(cv_folder) != "CVs":
            return

        jd_files = [f for f in os.listdir(position_folder) if f.lower().endswith(".pdf")]
        if len(jd_files) != 1:
            rprint(f"[bold yellow]Cannot process {cv_path}: No single JD found in {position_folder}.[/bold yellow]")
            return

        jd_path = os.path.join(position_folder, jd_files[0])
        
        try:
            jd_text = extract_text_from_pdf(jd_path)
        except Exception as e:
            rprint(f"[bold red]Error reading JD {jd_path}: {e}[/bold red]")
            return

        rprint(f"\n[bold green]New CV detected:[/bold green] {cv_filename}. Processing...")
        
        coro = process_single_cv_quietly(
            cv_path,
            jd_text,
            self.config,
            self.gemini_client,
            self.notion_manager,
            self.console,
        )
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        
        try:
            successful_files, _, _ = future.result(timeout=300)
            if successful_files:
                with open(processed_log_file, "a") as f:
                    for file_name in successful_files:
                        f.write(f"{file_name}\n")
        except Exception as e:
            rprint(f"[bold red]Error during background processing of {cv_filename}: {e}[/bold red]")
        
        rprint(f"[cyan]Monitoring '{self.jobs_folder}' for new CVs... (Press Ctrl+C to stop)[/cyan]")


async def watch_command(
    jobs_folder: str,
    notion_db_id: Optional[str],
    notion_api_key: Optional[str],
    gemini_api_key: Optional[str],
    gemini_model: Optional[str],
    gemini_temperature: Optional[float],
    max_gemini_concurrent: int,
    max_notion_concurrent: int,
    timezone: Optional[str],
    console: Console,
):
    """
    Monitors the jobs folder and processes new CVs as they are added.
    """
    rprint(Panel("[bold]Resume Analyzer Agent - Watch Mode[/bold]", expand=False))

    if not os.path.isdir(jobs_folder):
        rprint(f"[bold red]Error:[/bold red] The specified path '{jobs_folder}' is not a valid directory.")
        raise typer.Exit(code=1)

    clients = await initialize_clients(
        notion_db_id,
        notion_api_key,
        gemini_api_key,
        gemini_model,
        gemini_temperature,
        timezone,
    )

    rprint("\n[bold]Performing initial scan of existing files...[/bold]")
    await run_batch_processing(
        jobs_folder=jobs_folder,
        config=clients["config"],
        gemini_client=clients["gemini_client"],
        notion_manager=clients["notion_manager"],
        console=console,
        max_gemini_concurrent=max_gemini_concurrent,
        max_notion_concurrent=max_notion_concurrent,
    )

    loop = asyncio.get_running_loop()
    event_handler = CVEventHandler(
        config=clients["config"],
        clients=clients,
        loop=loop,
        jobs_folder=jobs_folder,
        console=console,
    )
    
    observer = Observer()
    observer.schedule(event_handler, jobs_folder, recursive=True)
    observer.start()
    
    rprint("\n[bold green]Initial scan complete. Watcher is now running.[/bold green]")
    rprint(f"[cyan]Monitoring '{jobs_folder}' for new CVs... (Press Ctrl+C to stop)[/cyan]")
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    rprint("\n[bold]Watcher stopped.[/bold]")
