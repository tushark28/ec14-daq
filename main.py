#!/usr/bin/env python3
"""
EC14 Data Acquisition System - Phase 1
Python port of TestPoint EC14 application for USB-1408FS-Plus

This is the main entry point for the EC14 application.
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ec14_daq.ui.main_window import main

if __name__ == "__main__":
    main()
