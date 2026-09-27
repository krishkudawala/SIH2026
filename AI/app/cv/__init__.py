"""Computer vision interfaces and modules for Mandi Nyaay."""

from app.cv.calibration import (
    MEASUREMENT_DOMAIN_PLANAR,
    PLANAR_LIMITATION_DISCLAIMER,
    compute_marker_homography,
    evaluate_reference_object_measurement,
    measure_planar_contour_mm,
    measure_planar_distance_mm,
    transform_points_to_metric_plane,
)
from app.cv.marker import (
    detect_marker,
    save_marker_debug_visualization,
    validate_marker_geometry,
)
from app.cv.quality import assess_image_quality
from app.cv.onnx_adapter import ONNXModelAdapter

__all__ = [
    "MEASUREMENT_DOMAIN_PLANAR",
    "PLANAR_LIMITATION_DISCLAIMER",
    "ONNXModelAdapter",
    "assess_image_quality",
    "compute_marker_homography",
    "detect_marker",
    "evaluate_reference_object_measurement",
    "measure_planar_contour_mm",
    "measure_planar_distance_mm",
    "save_marker_debug_visualization",
    "transform_points_to_metric_plane",
    "validate_marker_geometry",
]
