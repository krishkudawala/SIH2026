"""
Mandi Nyaay AI + Backend Final Product Package.

Provides offline-first produce grading, computer vision, statutory RulePacks,
tamper-evident cryptographic ledger, and FastAPI REST endpoints for Flutter.
"""

from app.engine import MandiNyaayEngine
from app.api.app import app

__all__ = ["MandiNyaayEngine", "app"]
__version__ = "0.1.0"
