#!/usr/bin/env python3
"""
Simple runner script for MarkMark.
This avoids the need for setuptools installation during development.
"""

import sys
import os

# Add the script directory to Python path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

# Now run the main module
from main import main

if __name__ == "__main__":
    sys.exit(main())
