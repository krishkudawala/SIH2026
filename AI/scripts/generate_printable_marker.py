"""
Generate a printable reference ArUco marker image for physical printing and verification.

WARNING:
This tool exists ONLY to generate a high-resolution printable marker with ruler markings
for physical printing and caliper verification.
DO NOT use the generated image file as synthetic field test data!
"""

import argparse
from pathlib import Path
import cv2
import numpy as np


def generate_printable_marker(
    marker_id: int = 0,
    marker_family: str = "DICT_4X4_50",
    resolution_px: int = 1000,
    output_path: str = "data/reference/printable_aruco_dict4x4_50_id0.png",
) -> Path:
    """
    Generate a high-resolution printable ArUco marker with border margin.
    """
    if not hasattr(cv2.aruco, marker_family):
        raise ValueError(f"Unknown ArUco dictionary: {marker_family}")

    dict_id = getattr(cv2.aruco, marker_family)
    dictionary = cv2.aruco.getPredefinedDictionary(dict_id)

    # 1. Generate marker core
    marker_core_size = int(resolution_px * 0.7)
    marker_img = cv2.aruco.generateImageMarker(dictionary, marker_id, marker_core_size)

    # 2. Embed into canvas with white margin
    canvas = np.full((resolution_px, resolution_px), 255, dtype=np.uint8)
    offset = (resolution_px - marker_core_size) // 2
    canvas[offset : offset + marker_core_size, offset : offset + marker_core_size] = marker_img

    # 3. Add verification annotations
    canvas_bgr = cv2.cvtColor(canvas, cv2.COLOR_GRAY2BGR)
    label = f"MANDI NYAAY PHYSICAL CALIBRATION REFERENCE -- {marker_family} ID:{marker_id}"
    warning = "MEASURE PRINTED OUTER EDGES WITH VERNIER CALIPER BEFORE FIELD USE"

    cv2.putText(canvas_bgr, label, (50, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2, cv2.LINE_AA)
    cv2.putText(canvas_bgr, warning, (50, resolution_px - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 200), 2, cv2.LINE_AA)

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_file), canvas_bgr)
    return out_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate printable ArUco marker for physical calibration")
    parser.add_argument("--id", type=int, default=0, help="ArUco marker ID (default: 0)")
    parser.add_argument("--family", type=str, default="DICT_4X4_50", help="ArUco dictionary (default: DICT_4X4_50)")
    parser.add_argument("--output", type=str, default="data/reference/printable_aruco_dict4x4_50_id0.png", help="Output PNG path")
    args = parser.parse_args()

    saved = generate_printable_marker(
        marker_id=args.id,
        marker_family=args.family,
        output_path=args.output,
    )
    print(f"Generated printable marker reference: {saved.resolve()}")
    print("NOTE: Print at 100% scale without 'fit to page'. Verify outer edge with vernier caliper.")


if __name__ == "__main__":
    main()
