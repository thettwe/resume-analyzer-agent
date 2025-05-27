import mimetypes
import os
from datetime import datetime
from typing import Optional

import aiohttp
from notion_client import AsyncClient as NotionClient
from rich import print as rprint
from pytz import timezone as tzinfo
from api.models import Candidate


class NotionManager:
    def __init__(self, token: str, database_id: str, timezone: str = "UTC"):
        """
        Initialize the Notion manager.

        Args:
            token: Notion API token
            database_id: ID of the Notion database
            timezone: Timezone for date/time formatting (default: UTC)
        """
        self.client = None
        self.token = token
        self.database_id = database_id
        self.timezone = tzinfo(timezone) if timezone else None

    async def configure(self):
        """
        Configure the Notion client.
        """
        self.client = NotionClient(auth=self.token)
        await self.client.users.me()

        await self.client.databases.retrieve(database_id=self.database_id)

        return self

    async def check_for_duplicate(self, email: str) -> bool:
        """
        Check if a candidate with the given email already exists for this job.

        Args:
            email: Candidate's email
            job_location: Location

        Returns:
            True if a duplicate exists, False otherwise
        """
        if not email or email == "N/A":
            return False

        try:
            filter_params = {
                "filter": {
                    "and": [
                        {"property": "Email", "email": {"equals": email}},
                    ]
                }
            }

            response = await self.client.databases.query(
                database_id=self.database_id, **filter_params
            )
            return len(response.get("results", [])) > 0
        except Exception as e:
            rprint(f"\n[bold red]Error checking for duplicate: {str(e)}[/bold red]")
            # If there's an error, assume no duplicate to allow creation
            return False

    async def upload_file_to_notion(self, file_path: str) -> Optional[str]:
        """
        Upload a file to Notion using the two-step process with aiohttp.

        Args:
            file_path: Path to the file to upload

        Returns:
            URL of the uploaded file or None if upload failed
        """
        try:
            # Get file name and size
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)

            # Common headers for all Notion API requests
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json",
            }

            async with aiohttp.ClientSession() as session:
                # Step 1: Create upload request to get upload ID
                async with session.post(
                    "https://api.notion.com/v1/file_uploads",
                    headers=headers,
                    json={"name": file_name, "size": file_size},
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        rprint(
                            f"\n[bold red]Failed to initiate file upload: {error_text}[/bold red]"
                        )
                        return None

                    upload_data = await response.json()
                    file_upload_id = upload_data.get("id")

                    if not file_upload_id:
                        rprint(
                            "\n[bold red]Failed to get file upload ID from response[/bold red]"
                        )
                        return None

                # Step 2: Upload the file content
                # Remove Content-Type from headers for multipart request
                upload_headers = {
                    k: v for k, v in headers.items() if k != "Content-Type"
                }

                # Determine content type of the file
                content_type, _ = mimetypes.guess_type(file_path)
                if not content_type:
                    content_type = "application/octet-stream"

                with open(file_path, "rb") as f:
                    file_content = f.read()

                form = aiohttp.FormData()
                form.add_field(
                    "file", file_content, filename=file_name, content_type=content_type
                )

                async with session.post(
                    f"https://api.notion.com/v1/file_uploads/{file_upload_id}/send",
                    headers=upload_headers,
                    data=form,
                ) as upload_response:
                    if upload_response.status != 200:
                        error_text = await upload_response.text()
                        rprint(
                            f"\n[bold red]Failed to upload file content: {error_text}[/bold red]"
                        )
                        return None

                    result = await upload_response.json()
                    return result

        except Exception as e:
            rprint(f"\n[bold red]Error uploading file to Notion: {str(e)}[/bold red]")
            return None

    async def create_candidate_row(
        self, candidate: Candidate, cv_filepath: str
    ) -> Optional[str]:
        """
        Create a new row in the Notion database table for the candidate.

        Args:
            candidate: Candidate data
            cv_filepath: Path to the CV file
            position_title: Position title from JD
            job_location: Job Location from JD

        Returns:
            ID of the created row or None if creation failed
        """
        attempts = 0
        max_attempts = 5
        while attempts < max_attempts:
            try:
                # Upload the file and get response
                file_upload = await self.upload_file_to_notion(cv_filepath)

                # Prepare properties with correct CV file handling
                properties = {
                    "Name": {"title": [{"text": {"content": candidate.full_name}}]},
                    "Email": {"email": candidate.email},
                    "Phone": {"phone_number": candidate.contact_number},
                    "Linkedin": {"url": candidate.linkedin_url},
                    "Gender": {"select": {"name": candidate.gender}},
                    "YOE": {"number": candidate.years_of_experience},
                    "Profile Summary": {
                        "rich_text": [
                            {"text": {"content": candidate.experience_summary}}
                        ]
                    },
                    "Professional Skills": {
                        "multi_select": [
                            {"name": skill.replace(",", "")}
                            for skill in candidate.professional_skills
                        ]
                    },
                    "Personal Skills": {
                        "multi_select": [
                            {"name": skill.replace(",", "")}
                            for skill in candidate.personal_skills
                        ]
                    },
                    "CV File": {
                        "files": [
                            {
                                "type": "file_upload",
                                "file_upload": {"id": file_upload.get("id")},
                            }
                        ]
                    },
                    "Position Title": {
                        "select": {"name": candidate.job_position_title}
                    },
                    "Location": {"select": {"name": candidate.job_location}},
                    "Match Score": {"number": candidate.match_score},
                    "Ranking Category": {
                        "select": {"name": candidate.ranking_category}
                    },
                    "AI Ranking Reason": {
                        "rich_text": [{"text": {"content": candidate.ranking_reason}}]
                    },
                    "Processing Date": {"date": {"start": datetime.now(tz=self.timezone).isoformat()}},
                    "Status": {"status": {"name": "Processed by AI"}},
                }

                if candidate.date_of_birth != "N/A":
                    properties["DOB"] = {"date": {"start": candidate.date_of_birth}}

                # Create a new row in the table
                response = await self.client.pages.create(
                    parent={"database_id": self.database_id}, properties=properties
                )

                return response["id"]

            except Exception as e:
                rprint(
                    f"\n[bold red]Error creating Notion table row: {str(e)}[/bold red]"
                )
                attempts += 1
                if attempts < max_attempts:
                    rprint("\n[bold yellow]Retrying...[/bold yellow]")
                else:
                    return None
