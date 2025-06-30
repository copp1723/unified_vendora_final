#!/usr/bin/env python3
"""
VENDORA - Automotive AI Data Platform
Main entry point launcher - delegates to src/main.py
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import and run the main application
if __name__ == '__main__':
    from main import *
    # The src/main.py will handle the actual application startup