"""
Local Offline Data Store for Mandi Nyaay (Gate 6B / Phases 20 & 21).

Provides pure local offline persistence for:
- Inspection sessions
- Lot records
- Capture metadata
- Observations and SampleUnits
- RulePacks and Decisions
- Dispute records
- Tamper-evident evidence packages

Guarantees:
- Zero cloud, server, or internet network dependencies.
- Deterministic JSON file persistence.
- Re-opening and replayability of completed inspections.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from pydantic import BaseModel

from app.domain.dispute import DisputeRecord
from app.domain.inspection_session import InspectionSession, LotInspectionResult


DEFAULT_STORAGE_DIR = Path("data/storage")


class LocalDataStore:
    """
    Local filesystem JSON persistence engine.
    Works 100% offline.
    """

    def __init__(self, root_dir: Path | str = DEFAULT_STORAGE_DIR):
        self.root_dir = Path(root_dir).resolve()
        self.sessions_dir = self.root_dir / "sessions"
        self.results_dir = self.root_dir / "results"
        self.disputes_dir = self.root_dir / "disputes"
        self.evidence_dir = self.root_dir / "evidence"

        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create storage hierarchy if not present."""
        for d in [self.sessions_dir, self.results_dir, self.disputes_dir, self.evidence_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def save_session(self, session: InspectionSession) -> Path:
        """Persist complete InspectionSession to offline JSON."""
        file_path = self.sessions_dir / f"{session.session_id}.json"
        data = session.model_dump(mode="json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True)
        return file_path

    def load_session(self, session_id: str) -> InspectionSession:
        """Load an InspectionSession by ID from local disk."""
        file_path = self.sessions_dir / f"{session_id}.json"
        if not file_path.exists():
            raise FileNotFoundError(f"Session file not found: {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return InspectionSession.model_validate(data)

    def list_session_ids(self) -> list[str]:
        """List all stored inspection session IDs."""
        return sorted([p.stem for p in self.sessions_dir.glob("*.json")])

    def save_lot_result(self, result: LotInspectionResult) -> Path:
        """Persist LotInspectionResult to offline JSON."""
        file_path = self.results_dir / f"{result.lot_id}_{result.session_id}.json"
        data = result.model_dump(mode="json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True)
        return file_path

    def load_lot_result(self, lot_id: str, session_id: str) -> LotInspectionResult:
        """Load a LotInspectionResult from disk."""
        file_path = self.results_dir / f"{lot_id}_{session_id}.json"
        if not file_path.exists():
            raise FileNotFoundError(f"Lot result file not found: {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return LotInspectionResult.model_validate(data)

    def save_dispute(self, dispute: DisputeRecord) -> Path:
        """Persist DisputeRecord to offline JSON."""
        file_path = self.disputes_dir / f"{dispute.dispute_id}.json"
        data = dispute.model_dump(mode="json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True)
        return file_path

    def load_dispute(self, dispute_id: str) -> DisputeRecord:
        """Load DisputeRecord from disk."""
        file_path = self.disputes_dir / f"{dispute_id}.json"
        if not file_path.exists():
            raise FileNotFoundError(f"Dispute file not found: {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return DisputeRecord.model_validate(data)

    def list_dispute_ids(self) -> list[str]:
        """List all stored dispute IDs."""
        return sorted([p.stem for p in self.disputes_dir.glob("*.json")])
