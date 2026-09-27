"""
SQLite Storage Manager using SQLModel for Mandi Nyaay (Gate 8 & Feature 20).

Provides offline, ACID-compliant persistence for all inspection entities:
- Sessions, Captures, Observations, SampleUnits
- ReviewSignals, Decisions, Disputes
- Cryptographic Event Ledger
- Physical Calibration Records
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Sequence
from sqlmodel import Session, SQLModel, create_engine, select

from app.storage.sql_models import (
    CalibrationSampleModel,
    CaptureModel,
    DecisionModel,
    DisputeModel,
    EventLedgerModel,
    ObservationModel,
    ReviewSignalModel,
    SampleUnitModel,
    SessionModel,
)

DEFAULT_DB_PATH = Path("data/storage/mandi_nyaay.db")


class SQLStore:
    """
    SQLModel SQLite Database interface for Mandi Nyaay.
    Runs 100% offline with zero cloud/network dependency.
    """

    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH):
        self.db_path = Path(db_path).resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        sqlite_url = f"sqlite:///{self.db_path.as_posix()}"
        self.engine = create_engine(sqlite_url, echo=False, connect_args={"check_same_thread": False})
        self.init_db()

    def init_db(self) -> None:
        """Create all tables in SQLite database if they do not exist and migrate missing columns."""
        SQLModel.metadata.create_all(self.engine)
        self._migrate_columns()

    def _migrate_columns(self) -> None:
        """Safely add any newly declared columns to existing SQLite tables."""
        from sqlalchemy import text
        with self.engine.connect() as conn:
            for table_name, table in SQLModel.metadata.tables.items():
                res = conn.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
                existing_cols = {row[1] for row in res}
                if not existing_cols:
                    continue
                for col in table.columns:
                    if col.name not in existing_cols:
                        col_type = col.type.compile(self.engine.dialect)
                        conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col.name} {col_type}"))
            conn.commit()

    def get_session(self) -> Session:
        """Yield a new SQLModel database session."""
        return Session(self.engine)

    # 1. Inspection Sessions
    def save_session(self, session_model: SessionModel) -> SessionModel:
        with Session(self.engine, expire_on_commit=False) as session:
            existing = session.get(SessionModel, session_model.id)
            if existing:
                for k, v in session_model.model_dump().items():
                    setattr(existing, k, v)
                session.add(existing)
                session.commit()
                session.refresh(existing)
                return existing
            else:
                session.add(session_model)
                session.commit()
                session.refresh(session_model)
                return session_model

    def get_session_by_id(self, session_id: str) -> SessionModel | None:
        with Session(self.engine, expire_on_commit=False) as session:
            return session.get(SessionModel, session_id)

    def list_sessions(self, limit: int = 100) -> list[SessionModel]:
        with Session(self.engine, expire_on_commit=False) as session:
            statement = select(SessionModel).order_by(SessionModel.created_at.desc()).limit(limit)  # type: ignore
            return list(session.exec(statement).all())

    # 2. Captures
    def add_capture(self, capture: CaptureModel) -> CaptureModel:
        with Session(self.engine, expire_on_commit=False) as session:
            session.add(capture)
            session.commit()
            session.refresh(capture)
            return capture

    def get_captures_for_session(self, session_id: str) -> list[CaptureModel]:
        with Session(self.engine, expire_on_commit=False) as session:
            statement = select(CaptureModel).where(CaptureModel.session_id == session_id).order_by(CaptureModel.captured_at.asc())  # type: ignore
            return list(session.exec(statement).all())

    # 3. Sample Units
    def save_sample_units(self, units: Sequence[SampleUnitModel]) -> None:
        with Session(self.engine, expire_on_commit=False) as session:
            for u in units:
                existing = session.get(SampleUnitModel, u.id)
                if existing:
                    for k, v in u.model_dump().items():
                        setattr(existing, k, v)
                    session.add(existing)
                else:
                    session.add(u)
            session.commit()

    def get_sample_units_for_session(self, session_id: str) -> list[SampleUnitModel]:
        with Session(self.engine, expire_on_commit=False) as session:
            statement = select(SampleUnitModel).where(SampleUnitModel.session_id == session_id).order_by(SampleUnitModel.created_at.asc())  # type: ignore
            return list(session.exec(statement).all())

    # 4. Observations
    def save_observations(self, observations: Sequence[ObservationModel]) -> None:
        with Session(self.engine, expire_on_commit=False) as session:
            for obs in observations:
                existing = session.get(ObservationModel, obs.id)
                if existing:
                    for k, v in obs.model_dump().items():
                        setattr(existing, k, v)
                    session.add(existing)
                else:
                    session.add(obs)
            session.commit()

    def get_observations_for_session(self, session_id: str) -> list[ObservationModel]:
        with Session(self.engine, expire_on_commit=False) as session:
            statement = select(ObservationModel).where(ObservationModel.session_id == session_id)
            return list(session.exec(statement).all())

    # 5. Review Signals
    def save_review_signals(self, signals: Sequence[ReviewSignalModel]) -> None:
        with Session(self.engine, expire_on_commit=False) as session:
            for sig in signals:
                existing = session.get(ReviewSignalModel, sig.id)
                if not existing:
                    session.add(sig)
            session.commit()

    def get_review_signals_for_session(self, session_id: str) -> list[ReviewSignalModel]:
        with Session(self.engine, expire_on_commit=False) as session:
            statement = select(ReviewSignalModel).where(ReviewSignalModel.session_id == session_id).order_by(ReviewSignalModel.created_at.asc())  # type: ignore
            return list(session.exec(statement).all())

    # 6. Decisions
    def save_decision(self, decision: DecisionModel) -> DecisionModel:
        with Session(self.engine, expire_on_commit=False) as session:
            existing = session.exec(select(DecisionModel).where(DecisionModel.session_id == decision.session_id)).first()
            if existing:
                for k, v in decision.model_dump().items():
                    setattr(existing, k, v)
                session.add(existing)
                session.commit()
                session.refresh(existing)
                return existing
            else:
                session.add(decision)
                session.commit()
                session.refresh(decision)
                return decision

    def get_decision_for_session(self, session_id: str) -> DecisionModel | None:
        with Session(self.engine, expire_on_commit=False) as session:
            return session.exec(select(DecisionModel).where(DecisionModel.session_id == session_id)).first()

    # 7. Disputes
    def save_dispute(self, dispute: DisputeModel) -> DisputeModel:
        with Session(self.engine, expire_on_commit=False) as session:
            existing = session.get(DisputeModel, dispute.id)
            if existing:
                for k, v in dispute.model_dump().items():
                    setattr(existing, k, v)
                session.add(existing)
                session.commit()
                session.refresh(existing)
                return existing
            else:
                session.add(dispute)
                session.commit()
                session.refresh(dispute)
                return dispute

    def get_dispute_by_id(self, dispute_id: str) -> DisputeModel | None:
        with Session(self.engine, expire_on_commit=False) as session:
            return session.get(DisputeModel, dispute_id)

    def get_dispute_for_session(self, session_id: str) -> DisputeModel | None:
        with Session(self.engine, expire_on_commit=False) as session:
            return session.exec(select(DisputeModel).where(DisputeModel.primary_session_id == session_id)).first()

    # 8. Event Timeline
    def append_event(self, event: EventLedgerModel) -> EventLedgerModel:
        with Session(self.engine, expire_on_commit=False) as session:
            session.add(event)
            session.commit()
            session.refresh(event)
            return event

    def get_events_for_session(self, session_id: str) -> list[EventLedgerModel]:
        with Session(self.engine, expire_on_commit=False) as session:
            statement = select(EventLedgerModel).where(EventLedgerModel.session_id == session_id).order_by(EventLedgerModel.sequence_number.asc())  # type: ignore
            return list(session.exec(statement).all())

    # 9. Calibration Samples
    def add_calibration_sample(self, sample: CalibrationSampleModel) -> CalibrationSampleModel:
        with Session(self.engine, expire_on_commit=False) as session:
            session.add(sample)
            session.commit()
            session.refresh(sample)
            return sample

    def list_calibration_samples(self) -> list[CalibrationSampleModel]:
        with Session(self.engine, expire_on_commit=False) as session:
            statement = select(CalibrationSampleModel).order_by(CalibrationSampleModel.created_at.asc())  # type: ignore
            return list(session.exec(statement).all())
