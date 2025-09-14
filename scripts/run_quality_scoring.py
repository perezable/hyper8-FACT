#!/usr/bin/env python3
"""
FACT Knowledge Base Quality Scoring Runner

This script executes the quality scoring analysis and generates 
the deployment-ready knowledge base with the top 200 entries.
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from quality_scoring.quality_specialist import QualitySpecialist, main

if __name__ == "__main__":
    # Run the quality specialist
    main()