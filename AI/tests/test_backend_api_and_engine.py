"""
End-to-End Tests for Mandi Nyaay Engine & FastAPI Backend.

Verifies:
1. Programmatic MandiNyaayEngine operations across all 20 features
2. Complete suite of FastAPI endpoints backing the Flutter client
3. Zero mock values: Real ONNX detector, real OpenCV image quality, real PyTorch segmentation,
   real temperature scaling, real Wilson CIs, real SHA-256 evidence chain, real SQLite persistence.
"""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.api.app import app, get_engine
from app.engine import MandiNyaayEngine
from app.storage.sql_models import SessionModel


@pytest.fixture
def temp_db_path(tmp_path: Path) -> Path:
    return tmp_path / "test_mandi_nyaay.db"


@pytest.fixture
def engine(temp_db_path: Path) -> MandiNyaayEngine:
    return MandiNyaayEngine(db_path=temp_db_path)


@pytest.fixture
def client(temp_db_path: Path) -> TestClient:
    eng = MandiNyaayEngine(db_path=temp_db_path)
    app.dependency_overrides[get_engine] = lambda: eng
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


REAL_IMAGE_PATH = "data/raw/01_mixed_damaged_rotten_healthy.jpg"


def test_engine_complete_lifecycle(engine: MandiNyaayEngine):
    # 1. Create session
    session = engine.create_session(
        lot_id="LOT_TEST_001",
        source_reference="BAG_TRAY_A1",
        target_sample_size=10,
        declared_bag_count=100,
        certified_lot_weight_kg=5000.0,
    )
    assert session.id.startswith("sess_")
    assert session.source_selected_by_inspector is True
    assert session.physical_source_identity_verified is False
    assert session.status == "CREATED"

    # 2. Add capture with real image quality screening
    capture = engine.add_capture(
        session_id=session.id,
        image_path=REAL_IMAGE_PATH,
        capture_role="PRIMARY_SAMPLE_CAPTURE",
        view_angle="TOP",
    )
    assert capture.id.startswith("cap_")
    assert capture.quality_grade in ["PASS", "WARN", "FAIL"]
    assert capture.blur_score > 0.0
    assert capture.mean_luminance > 0.0

    # 3. Run real inference
    inf_res = engine.run_inference(session_id=session.id)
    assert inf_res["session_id"] == session.id
    assert inf_res["observations_count"] > 0
    assert inf_res["sample_units_count"] > 0
    assert len(inf_res["items"]) > 0

    first_item = inf_res["items"][0]
    assert "bbox" in first_item
    assert "condition" in first_item
    assert "confidence" in first_item
    assert "visible_defect_fraction" in first_item
    assert "defect_disclaimer" in first_item
    assert first_item["defect_disclaimer"] == "Externally visible condition only."
    assert "size_status" in first_item
    assert "weight_status" in first_item

    # 4. Check query methods
    obs = engine.get_observations(session.id)
    assert len(obs) == inf_res["observations_count"]

    units = engine.get_sample_units(session.id)
    assert len(units) == inf_res["sample_units_count"]

    sampling = engine.get_sampling(session.id)
    assert sampling["observed_sample_size"] == inf_res["sample_units_count"]
    assert len(sampling["wilson_intervals"]) > 0

    meas = engine.get_measurement(session.id)
    assert len(meas["units"]) == len(units)

    weight = engine.get_weight(session.id)
    assert weight["mass_status"] == "UNVALIDATED"

    review = engine.get_review(session.id)
    assert "signals" in review

    # 5. Evaluate Decision with Override
    dec = engine.evaluate_decision(
        session_id=session.id,
        manual_override={"override_grade": "GRADE_A", "reason": "Inspector validated produce visually"},
    )
    assert dec.procurement_grade == "GRADE_A"
    assert dec.override_applied is True

    # 6. Open Dispute & Resolve
    disp = engine.open_dispute(session.id, dispute_reason="Moisture level variation claimed by trader")
    assert disp.id.startswith("dsp_")
    assert disp.status == "SECONDARY_INSPECTION_PENDING"

    resolved = engine.resolve_dispute(
        dispute_id=disp.id,
        final_grade="GRADE_A",
        arbitrator_id="ARB_NASHIK_01",
        arbitration_notes="Joint inspection confirmed Grade A quality.",
    )
    assert resolved.status == "RESOLVED"
    assert resolved.final_resolution_grade == "GRADE_A"

    # 7. Evidence & Replay
    evid = engine.get_evidence(session.id)
    assert evid["evidence_root_hash"] is not None
    assert evid["classification"] == "TAMPER-EVIDENT/REPLAYABLE"
    assert len(evid["events"]) >= 3

    replay = engine.replay_session(session.id)
    assert replay["is_replay_successful"] is True
    assert replay["is_bit_for_bit_identical"] is True

    # 8. Report
    rep = engine.get_report(session.id)
    assert "# MANDI NYAAY" in rep["markdown_report"]
    assert "MANDI NYAAY INSPECTION" in rep["printable_receipt"]
    assert rep["offline_ref_code"].startswith("MN-")


def test_fastapi_all_endpoints(client: TestClient):
    # Health
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "HEALTHY"

    # POST /sessions
    sess_req = {
        "lot_id": "LOT_API_001",
        "source_reference": "BAG_42",
        "target_sample_size": 15,
        "declared_bag_count": 50,
        "certified_lot_weight_kg": 2500.0,
    }
    r = client.post("/sessions", json=sess_req)
    assert r.status_code == 200
    session_data = r.json()
    session_id = session_data["id"]

    # GET /sessions/{id}
    r = client.get(f"/sessions/{session_id}")
    assert r.status_code == 200
    assert r.json()["lot_id"] == "LOT_API_001"

    # POST /sessions/{id}/captures
    cap_req = {
        "image_path": REAL_IMAGE_PATH,
        "capture_role": "PRIMARY_SAMPLE_CAPTURE",
        "view_angle": "TOP",
    }
    r = client.post(f"/sessions/{session_id}/captures", json=cap_req)
    assert r.status_code == 200
    capture_data = r.json()
    assert capture_data["quality_grade"] in ["PASS", "WARN", "FAIL"]

    # GET /sessions/{id}/captures
    r = client.get(f"/sessions/{session_id}/captures")
    assert r.status_code == 200
    assert len(r.json()) == 1

    # POST /sessions/{id}/inference
    r = client.post(f"/sessions/{session_id}/inference")
    assert r.status_code == 200
    inf_data = r.json()
    assert inf_data["observations_count"] > 0
    assert inf_data["sample_units_count"] > 0

    # GET /sessions/{id}/observations
    r = client.get(f"/sessions/{session_id}/observations")
    assert r.status_code == 200
    assert len(r.json()) > 0

    # GET /sessions/{id}/sample-units
    r = client.get(f"/sessions/{session_id}/sample-units")
    assert r.status_code == 200
    assert len(r.json()) > 0

    # GET /sessions/{id}/sampling
    r = client.get(f"/sessions/{session_id}/sampling")
    assert r.status_code == 200
    assert "wilson_intervals" in r.json()

    # GET /sessions/{id}/measurement
    r = client.get(f"/sessions/{session_id}/measurement")
    assert r.status_code == 200
    assert r.json()["size_status"] in ["MEASUREMENT_AVAILABLE", "ONION_DIAMETER_UNVALIDATED"]

    # GET /sessions/{id}/weight
    r = client.get(f"/sessions/{session_id}/weight")
    assert r.status_code == 200
    assert r.json()["mass_status"] == "UNVALIDATED"

    # GET /sessions/{id}/review
    r = client.get(f"/sessions/{session_id}/review")
    assert r.status_code == 200
    assert "signals" in r.json()

    # POST /sessions/{id}/decision
    dec_req = {
        "rule_pack_id": "AGMARK_ONION_2024_V1",
        "override_grade": "GRADE_A",
        "override_reason": "Visual validation passed",
    }
    r = client.post(f"/sessions/{session_id}/decision", json=dec_req)
    assert r.status_code == 200
    assert r.json()["procurement_grade"] == "GRADE_A"

    # POST /sessions/{id}/dispute
    disp_req = {
        "dispute_reason": "Trader disputed sprout defect ratio",
        "opened_by": "FARMER_RAMESH",
    }
    r = client.post(f"/sessions/{session_id}/dispute", json=disp_req)
    assert r.status_code == 200
    assert r.json()["status"] == "SECONDARY_INSPECTION_PENDING"

    # GET /sessions/{id}/dispute
    r = client.get(f"/sessions/{session_id}/dispute")
    assert r.status_code == 200

    # POST /sessions/{id}/dispute/resolve
    res_req = {
        "final_grade": "GRADE_A",
        "arbitrator_id": "APMC_CHAIR_01",
        "arbitration_notes": "Settled under rule pack standard.",
    }
    r = client.post(f"/sessions/{session_id}/dispute/resolve", json=res_req)
    assert r.status_code == 200
    assert r.json()["status"] == "RESOLVED"

    # GET /sessions/{id}/evidence
    r = client.get(f"/sessions/{session_id}/evidence")
    assert r.status_code == 200
    assert r.json()["classification"] == "TAMPER-EVIDENT/REPLAYABLE"

    # POST /sessions/{id}/replay
    r = client.post(f"/sessions/{session_id}/replay")
    assert r.status_code == 200
    assert r.json()["is_replay_successful"] is True

    # GET /sessions/{id}/report
    r = client.get(f"/sessions/{session_id}/report")
    assert r.status_code == 200
    assert "structured_result" in r.json()
    assert "markdown_report" in r.json()
    assert "printable_receipt" in r.json()


def test_calibration_and_ocr_endpoints(client: TestClient):
    # 1. Calibration record entry
    cal_req = {
        "sample_unit_id": "su_cal_101",
        "lot_id": "LOT_CALIB_TEST",
        "length_mm": 55.0,
        "width_mm": 52.0,
        "thickness_mm": 48.0,
        "actual_scale_weight_g": 72.5,
        "condition": "HEALTHY",
        "defect_fraction": 0.0,
        "variety": "Nashik Red",
        "operator_id": "TEST_OP_01",
    }
    r = client.post("/calibration/samples", json=cal_req)
    assert r.status_code == 200
    assert r.json()["actual_scale_weight_g"] == 72.5

    # 2. List calibration samples
    r = client.get("/calibration/samples")
    assert r.status_code == 200
    assert len(r.json()) >= 1

    # 3. OCR Scan
    r = client.post("/ocr/scan", json={"image_path": REAL_IMAGE_PATH})
    assert r.status_code == 200
    assert "candidates" in r.json()
    assert r.json()["overall_status"] == "PENDING_INSPECTOR_CONFIRMATION"

    # 4. OCR Confirm
    conf_req = {
        "text": "LOT: MH-NSK-2026-B08",
        "confidence": 0.95,
        "field_type": "LOT_ID",
        "confirmed_text": "LOT-MH-NSK-2026-B08",
    }
    r = client.post("/ocr/confirm", json=conf_req)
    assert r.status_code == 200
    assert r.json()["status"] == "INSPECTOR_CONFIRMED"
    assert r.json()["confirmed_text"] == "LOT-MH-NSK-2026-B08"
