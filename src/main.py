import os
import sys

# This is the magic bit. It finds the project's root directory by
# taking the directory of this file (__file__), which is `src`, and
# going one level up. It then adds this root directory to the front
# of Python's search path.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Now that the project root is in the path, this import will work correctly.
from src.app import app

if __name__ == "__main__":
    app()