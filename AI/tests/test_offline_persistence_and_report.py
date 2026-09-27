"""
Tests for Offline Local Data Store and Report Generation.
"""

from pathlib import Path
import tempfile
import pytest

from app.domain.inspection_session import (
    ProcurementGrade,
    build_lot_inspection_result,
)
from app.reports.offline_report import (
    generate_compact_offline_reference,
    generate_offline_markdown_report,
    generate_printable_receipt_text,
)
from app.storage.local_store import LocalDataStore
from tests.test_dispute_and_replay import sample_session


def test_offline_local_data_store(sample_session, tmp_path):
    store = LocalDataStore(root_dir=tmp_path)

    # Save session
    saved_path = store.save_session(sample_session)
    assert saved_path.exists()
    assert sample_session.session_id in store.list_session_ids()

    # Load session
    loaded = store.load_session(sample_session.session_id)
    assert loaded.session_id == sample_session.session_id
    assert loaded.lot_id == sample_session.lot_id
    assert loaded.evidence_summary.evidence_root_hash == sample_session.evidence_summary.evidence_root_hash


def test_offline_report_and_receipt_generation(sample_session):
    lot_res = build_lot_inspection_result(sample_session, source_reference="BAG_TEST_01")

    # Offline compact reference code
    ref_code = generate_compact_offline_reference(lot_res.session_id, lot_res.evidence_root_hash)
    assert ref_code.startswith("MN-")
    assert "http" not in ref_code

    # Markdown certificate
    md = generate_offline_markdown_report(lot_res)
    assert "MANDI NYAAY — OFFICIAL PRODUCE INSPECTION CERTIFICATE" in md
    assert "TAMPER-EVIDENT / REPLAYABLE" in md
    assert "http" not in md  # Zero fake cloud URLs
    assert lot_res.lot_id in md
    assert "Source selected by inspector" in md

    # Thermal receipt
    receipt = generate_printable_receipt_text(lot_res)
    assert "MANDI NYAAY INSPECTION" in receipt
    assert "PRODUCE AUDIT RECEIPT" in receipt
    assert "http" not in receipt
    assert lot_res.decision.value in receipt
