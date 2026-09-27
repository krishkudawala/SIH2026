"""
Offline Inspection Report & Receipt Generator for Mandi Nyaay (Gate 6B / Phase 22).

Generates complete, human-readable offline inspection receipts and markdown certificates.

ANTI-FABRICATION RULE:
QR / Reference code ONLY encodes a compact offline session identifier and evidence digest.
NEVER generates fake cloud URLs.
Works 100% offline.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from app.domain.inspection_session import (
    InspectionSession,
    LotInspectionResult,
)


def generate_compact_offline_reference(session_id: str, evidence_hash: str) -> str:
    """
    Generate a compact offline alphanumeric reference code for printing / receipt.
    Format: MN-{session_prefix}-{hash_prefix}
    Zero cloud URLs.
    """
    clean_sid = session_id.replace("sess_", "").replace("-", "")[:8].upper()
    clean_hash = evidence_hash[:12].upper()
    return f"MN-{clean_sid}-{clean_hash}"


def generate_offline_markdown_report(result: LotInspectionResult) -> str:
    """
    Generate an offline markdown procurement inspection report.
    """
    compact_ref = generate_compact_offline_reference(
        result.session_id, result.evidence_root_hash or "000000000000"
    )

    signals_list = "\n".join(
        [f"- **[{s.severity.value}] {s.code.value}**: {s.message}" for s in result.review_signals]
    ) if result.review_signals else "- None (Clean inspection session)"

    decision_reasons = "\n".join([f"- {r}" for r in result.decision_reasons]) if result.decision_reasons else "- Standard rule thresholds satisfied."
    blocking_reasons = "\n".join([f"- {b}" for b in result.blocking_reasons]) if result.blocking_reasons else "- None"

    return f"""# MANDI NYAAY — OFFICIAL PRODUCE INSPECTION CERTIFICATE
**Audit Integrity**: TAMPER-EVIDENT / REPLAYABLE  
**Offline Reference**: `{compact_ref}`  
**Generated At**: {result.inspection_timestamp}

---

## 1. LOT & PROVENANCE
- **Lot ID**: `{result.lot_id}`
- **Session ID**: `{result.session_id}`
- **Physical Source**: `{result.source_reference}`
- **Traceability Disclaimer**: *{result.source_selection_note}*
- **Offline Evidence Root**: `{result.evidence_root_hash}`

---

## 2. STATISTICAL SAMPLING
- **Observed Sample Size**: **{result.sample_size}** physical bulbs
- **Target Sample Size**: **{result.target_sample_size}** bulbs
- **Shortfall / Remaining**: {result.remaining_sample_size} bulbs
- **Sampling Status**: **{result.sampling_status}**
- **Rationale**: {result.sampling_reason}

---

## 3. PHYSICAL CONDITION DISTRIBUTION (COUNT-BASED)
| Visible Condition | Count | Percentage |
| :--- | :---: | :---: |
| **Healthy** | {result.healthy_count} | {result.healthy_pct:.1f}% |
| **Visible Damage** | {result.damaged_count} | {result.damaged_pct:.1f}% |
| **Visible Sprouting** | {result.sprouted_count} | {result.sprouted_pct:.1f}% |
| **Visible Rot** | {result.rotten_count} | {result.rotten_pct:.1f}% |
| **Class Conflicts** | {result.class_conflict_count} | — |
| **Total Visible Defects** | — | **{result.total_defect_pct:.1f}%** |

*Note: Percentages describe externally visible condition only. Internal quality is not certified.*

---

## 4. METRIC & MASS STATUS
- **Size / Diameter Status**: `{result.size_status}`
- **Mass / Weight Status**: `{result.mass_status}`
- **Sizing Disclaimer**: *Planar homography does NOT establish true 3D onion diameter. FIELD_VALIDATION_PENDING.*
- **Mass Disclaimer**: *Volumetric mass estimation is unvalidated. Grading remains strictly count-based.*

---

## 5. STATUTORY RULE PACK & DECISION
- **Rule Pack**: `{result.rule_pack_id or 'DEFAULT_AGMARK'}` (v{result.rule_pack_version or '1.0.0'})
- **Procurement Grade Awarded**: **{result.decision.value}**
- **Decision Status**: `{result.decision_status}`

### Decision Rationale:
{decision_reasons}

### Blocking Conditions:
{blocking_reasons}

---

## 6. ACTIVE REVIEW SIGNALS
{signals_list}

---
*MANDI NYAAY CORE V1.0 — 100% OFFLINE SECURE INSPECTION ENGINE*
"""


def generate_printable_receipt_text(result: LotInspectionResult) -> str:
    """
    Generate clean, 40-column monospace receipt text suitable for standard thermal printers.
    """
    compact_ref = generate_compact_offline_reference(
        result.session_id, result.evidence_root_hash or "000000000000"
    )
    lines = [
        "========================================",
        "          MANDI NYAAY INSPECTION        ",
        "         PRODUCE AUDIT RECEIPT          ",
        "========================================",
        f"LOT ID   : {result.lot_id}",
        f"DATE/TIME: {result.inspection_timestamp[:19]}",
        f"REF CODE : {compact_ref}",
        "----------------------------------------",
        f"SOURCE   : {result.source_reference}",
        "NOTE     : Bag selected by inspector.",
        "           Physical identity unverified.",
        "----------------------------------------",
        f"SAMPLE   : {result.sample_size} / {result.target_sample_size} (Status: {result.sampling_status})",
        "----------------------------------------",
        "CONDITION BREAKDOWN (COUNT-BASED):",
        f"  HEALTHY  : {result.healthy_count:>4} ({result.healthy_pct:>5.1f}%)",
        f"  DAMAGED  : {result.damaged_count:>4} ({result.damaged_pct:>5.1f}%)",
        f"  SPROUTED : {result.sprouted_count:>4} ({result.sprouted_pct:>5.1f}%)",
        f"  ROTTEN   : {result.rotten_count:>4} ({result.rotten_pct:>5.1f}%)",
        f"  DEFECTS  :       {result.total_defect_pct:>5.1f}%",
        "----------------------------------------",
        f"SIZE STATUS : {result.size_status}",
        f"MASS STATUS : {result.mass_status}",
        "----------------------------------------",
        f"RULE PACK: {result.rule_pack_id or 'AGMARK'}",
        "----------------------------------------",
        "FINAL PROCUREMENT GRADE:",
        f"             >>> {result.decision.value} <<<",
        f"STATUS   : {result.decision_status}",
        "----------------------------------------",
        f"EVID HASH: {result.evidence_root_hash[:24]}...",
        "AUDIT    : TAMPER-EVIDENT / REPLAYABLE",
        "========================================",
    ]
    return "\n".join(lines)
