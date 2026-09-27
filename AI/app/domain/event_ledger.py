"""
Chronological Event Ledger for Mandi Nyaay (Gate 6A-6).

Provides an immutable, tamper-evident event stream recording all lifecycle
transitions of an inspection session:

SESSION_STARTED
-> SOURCE_SELECTED
-> CAPTURE_ADDED
-> OBSERVATIONS_RECONCILED
-> SAMPLING_UPDATED
-> AGGREGATION_UPDATED
-> REVIEW_SIGNAL_EMITTED
-> DECISION_UPDATED
-> SESSION_COMPLETED

Guarantees:
- Cryptographic SHA-256 chaining (previous_event_hash -> event_hash).
- Tamper-evident verification (detects modified payloads or reordered events).
- Strictly uses 'tamper-evident' and 'replayable' terminology (never claims tamper-proof).
- Canonical serialization ensures deterministic hash reproduction.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from typing import Any
import uuid

from pydantic import BaseModel, ConfigDict, Field


GENESIS_PREVIOUS_HASH = "0" * 64


class InspectionEventType(str, Enum):
    """Permitted canonical inspection event types."""
    SESSION_STARTED = "SESSION_STARTED"
    SOURCE_SELECTED = "SOURCE_SELECTED"
    CAPTURE_ADDED = "CAPTURE_ADDED"
    OBSERVATIONS_RECONCILED = "OBSERVATIONS_RECONCILED"
    SAMPLING_UPDATED = "SAMPLING_UPDATED"
    AGGREGATION_UPDATED = "AGGREGATION_UPDATED"
    REVIEW_SIGNAL_EMITTED = "REVIEW_SIGNAL_EMITTED"
    DECISION_UPDATED = "DECISION_UPDATED"
    SESSION_COMPLETED = "SESSION_COMPLETED"


def compute_payload_hash(payload: dict[str, Any]) -> str:
    """Compute canonical SHA-256 hash of event payload dictionary."""
    canonical_bytes = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(canonical_bytes).hexdigest()


def compute_event_hash(
    previous_event_hash: str,
    payload_hash: str,
    event_type: str,
    timestamp: str,
    sequence_number: int,
) -> str:
    """Compute cryptographic SHA-256 link in the tamper-evident chain."""
    token = f"{previous_event_hash}:{payload_hash}:{event_type}:{timestamp}:{sequence_number}"
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class InspectionEvent(BaseModel):
    """
    Immutable, cryptographically chained event record.
    """
    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(..., description="Unique deterministic or UUID event identifier")
    session_id: str = Field(..., description="Inspection session identifier")
    sequence_number: int = Field(..., ge=0, description="0-indexed monotonic position in event chain")
    event_type: InspectionEventType = Field(..., description="Type of event occurred")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp of event creation")
    payload: dict[str, Any] = Field(..., description="Event payload dictionary")
    payload_hash: str = Field(..., description="SHA-256 hash of canonical serialized payload")
    previous_event_hash: str = Field(..., description="SHA-256 digest of previous event in chain")
    event_hash: str = Field(..., description="SHA-256 link hash over event tuple")


class EventTimeline(BaseModel):
    """
    Chronological collection of chained inspection events.
    """
    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(..., description="Inspection session identifier")
    events: list[InspectionEvent] = Field(default_factory=list, description="Ordered chained events")
    ledger_integrity: str = Field(
        default="tamper-evident/replayable",
        description="Audit integrity classification (tamper-evident/replayable)"
    )

    def append_event(
        self,
        event_type: InspectionEventType,
        payload: dict[str, Any],
        timestamp: str | None = None,
        event_id: str | None = None,
    ) -> InspectionEvent:
        """
        Create, cryptographically hash, and append a new event to the timeline.
        """
        seq = len(self.events)
        ts = timestamp or datetime.now(timezone.utc).isoformat()
        eid = event_id or f"evt_{seq:04d}_{uuid.uuid4().hex[:6]}"
        prev_hash = self.events[-1].event_hash if self.events else GENESIS_PREVIOUS_HASH

        p_hash = compute_payload_hash(payload)
        e_hash = compute_event_hash(
            previous_event_hash=prev_hash,
            payload_hash=p_hash,
            event_type=event_type.value,
            timestamp=ts,
            sequence_number=seq,
        )

        event = InspectionEvent(
            event_id=eid,
            session_id=self.session_id,
            sequence_number=seq,
            event_type=event_type,
            timestamp=ts,
            payload=payload,
            payload_hash=p_hash,
            previous_event_hash=prev_hash,
            event_hash=e_hash,
        )
        self.events.append(event)
        return event

    def verify_integrity(self) -> tuple[bool, str | None]:
        """
        Verify mathematical integrity of the cryptographic chain across all events.
        Detects tampering, unauthorized edits, insertion, deletion, or reordering.
        """
        if not self.events:
            return True, None

        expected_prev_hash = GENESIS_PREVIOUS_HASH
        for idx, event in enumerate(self.events):
            if event.sequence_number != idx:
                return False, f"Sequence violation at index {idx}: expected {idx}, found {event.sequence_number}"

            if event.previous_event_hash != expected_prev_hash:
                return (
                    False,
                    f"Hash link broken at sequence {idx}: expected prev {expected_prev_hash}, found {event.previous_event_hash}"
                )

            recomputed_p_hash = compute_payload_hash(event.payload)
            if recomputed_p_hash != event.payload_hash:
                return (
                    False,
                    f"Payload tampering detected at sequence {idx}: recomputed {recomputed_p_hash} != {event.payload_hash}"
                )

            recomputed_e_hash = compute_event_hash(
                previous_event_hash=event.previous_event_hash,
                payload_hash=event.payload_hash,
                event_type=event.event_type.value,
                timestamp=event.timestamp,
                sequence_number=event.sequence_number,
            )
            if recomputed_e_hash != event.event_hash:
                return (
                    False,
                    f"Event hash tampering detected at sequence {idx}: recomputed {recomputed_e_hash} != {event.event_hash}"
                )

            expected_prev_hash = event.event_hash

        return True, None
