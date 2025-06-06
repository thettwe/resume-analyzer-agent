"""
Tests for utility functions
"""

import os
import sys

from rich.panel import Panel

# Add src directory to path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from misc.utils import format_processing_stats


class TestUtils:
    """Tests for utility functions."""

    def test_format_processing_stats_all_successful(self):
        """Test formatting processing stats with all successful files."""
        result = format_processing_stats(
            total_files=5,
            processed_files=5,
            successful_files=5,
            duplicate_files=0,
            failed_files=0,
            notion_db_id="test-db-id",
        )

        # Assert the result is a Panel
        assert isinstance(result, Panel)

        # Check for success indicators in the rendered text
        rendered = result.__str__()
        assert "Processing Complete" in rendered
        assert "5/5 files processed" in rendered
        assert "5 uploaded to Notion" in rendered
        assert "0 duplicates skipped" in rendered
        assert "0 failed" in rendered

    def test_format_processing_stats_with_duplicates(self):
        """Test formatting processing stats with duplicate files."""
        result = format_processing_stats(
            total_files=5,
            processed_files=5,
            successful_files=3,
            duplicate_files=2,
            failed_files=0,
            notion_db_id="test-db-id",
        )

        # Check for duplicate indicators in the rendered text
        rendered = result.__str__()
        assert "Processing Complete" in rendered
        assert "5/5 files processed" in rendered
        assert "3 uploaded to Notion" in rendered
        assert "2 duplicates skipped" in rendered
        assert "0 failed" in rendered

    def test_format_processing_stats_with_failures(self):
        """Test formatting processing stats with failed files."""
        result = format_processing_stats(
            total_files=5,
            processed_files=5,
            successful_files=2,
            duplicate_files=1,
            failed_files=2,
            notion_db_id="test-db-id",
        )

        # Check for failure indicators in the rendered text
        rendered = result.__str__()
        assert "Processing Complete" in rendered
        assert "5/5 files processed" in rendered
        assert "2 uploaded to Notion" in rendered
        assert "1 duplicates skipped" in rendered
        assert "2 failed" in rendered

    def test_format_processing_stats_partial_processing(self):
        """Test formatting processing stats with partial processing."""
        result = format_processing_stats(
            total_files=10,
            processed_files=5,
            successful_files=4,
            duplicate_files=1,
            failed_files=0,
            notion_db_id="test-db-id",
        )

        # Check for partial processing indicators in the rendered text
        rendered = result.__str__()
        assert "Processing Complete" in rendered
        assert "5/10 files processed" in rendered
        assert "4 uploaded to Notion" in rendered
        assert "1 duplicates skipped" in rendered
        assert "0 failed" in rendered
        assert "5 files were not processed" in rendered
