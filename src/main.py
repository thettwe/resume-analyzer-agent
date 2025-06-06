import os
import sys

# Add the src directory to path if needed
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from src.app import app
except ModuleNotFoundError:
    # When run directly with typer
    from app import app


if __name__ == "__main__":
    app()
