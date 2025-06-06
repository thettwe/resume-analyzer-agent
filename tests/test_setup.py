"""
Tests for the setup command
"""

import os
import sys
from unittest.mock import patch

# Add src directory to path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from commands.setup import setup_command


class TestSetupCommand:
    """Tests for setup command."""

    def test_setup_command(self):
        """Test setup command creates environment file."""
        with patch("commands.setup.create_env_example") as mock_create_env:
            # Call the function
            setup_command()

            # Verify that create_env_example was called
            mock_create_env.assert_called_once()
