"""
Verification script for Mandi Nyaay AI environment.

Confirms dependencies, domain models, and processing version can be loaded.
"""

import sys
import cv2
import numpy as np
import pydantic
import yaml

from app.domain import (
    CaptureInput,
    InspectionObservation,
    InspectionStatus,
    MarkerObservation,
    QualityFailureCode,
)
from app.version import get_processing_version


def main() -> None:
    print("=== Mandi Nyaay AI Inspection Core Environment ===")
    print(f"Python:            {sys.version.split()[0]}")
    print(f"OpenCV:            {cv2.__version__}")
    print(f"NumPy:             {np.__version__}")
    print(f"Pydantic:          {pydantic.__version__}")
    print(f"PyYAML:            {yaml.__version__}")
    print(f"Processing Version: {get_processing_version()}")
    print("Domain contracts loaded successfully.")


if __name__ == "__main__":
    main()
