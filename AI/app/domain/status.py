"""
Explicit failure and inspection status types.

Expected uncertainty and environmental degradation are modeled as explicit,
typed states rather than unexpected runtime exceptions.
"""

from enum import Enum


class InspectionStatus(str, Enum):
    """
    Core lifecycle and failure states for inspection observations.

    Guarantees no silent guessing or unrepresented failure modes.
    """
    VALID = "VALID"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    UNKNOWN = "UNKNOWN"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    RETRY = "RETRY"
    CALIBRATION_INVALID = "CALIBRATION_INVALID"
    INVALID_CAPTURE = "INVALID_CAPTURE"


class MarkerFailureCode(str, Enum):
    """Specific failure reasons for reference marker detection and calibration."""
    NONE = "NONE"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    MARKER_NOT_DETECTED = "MARKER_NOT_DETECTED"
    MARKER_ID_MISMATCH = "MARKER_ID_MISMATCH"
    GEOMETRY_INVALID = "GEOMETRY_INVALID"
    SIZE_UNRELIABLE = "SIZE_UNRELIABLE"
    MULTIPLE_MARKERS = "MULTIPLE_MARKERS"
    OCCLUDED = "OCCLUDED"


class QualityFailureCode(str, Enum):
    """Specific failure reasons for photographic and environmental capture quality."""
    NONE = "NONE"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    BLUR_EXCEEDED = "BLUR_EXCEEDED"
    UNDEREXPOSED = "UNDEREXPOSED"
    OVEREXPOSED = "OVEREXPOSED"
    LOW_CONTRAST = "LOW_CONTRAST"
    RESOLUTION_INSUFFICIENT = "RESOLUTION_INSUFFICIENT"


class MeasurementStatus(str, Enum):
    """Measurement outcome and uncertainty categorization."""
    # Gate 4B explicit status contract
    CALIBRATION_NOT_AVAILABLE = "CALIBRATION_NOT_AVAILABLE"
    CALIBRATION_INVALID = "CALIBRATION_INVALID"
    PLANAR_MEASUREMENT_AVAILABLE = "PLANAR_MEASUREMENT_AVAILABLE"
    ONION_DIAMETER_UNVALIDATED = "ONION_DIAMETER_UNVALIDATED"
    MEASUREMENT_AVAILABLE = "MEASUREMENT_AVAILABLE"
    MEASUREMENT_REQUIRES_REVIEW = "MEASUREMENT_REQUIRES_REVIEW"

    # Core lifecycle statuses
    VALID = "VALID"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    UNKNOWN = "UNKNOWN"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    RETRY = "RETRY"


class CalibrationStatus(str, Enum):
    """Explicit calibration readiness state."""
    CALIBRATION_NOT_AVAILABLE = "CALIBRATION_NOT_AVAILABLE"
    CALIBRATION_INVALID = "CALIBRATION_INVALID"
    PLANAR_METRIC_CALIBRATION_VALIDATED = "PLANAR_METRIC_CALIBRATION_VALIDATED"
    PHYSICAL_VALIDATION_BLOCKED = "PHYSICAL_VALIDATION_BLOCKED"


class OnionDiameterFeasibility(str, Enum):
    """Feasibility outcome for 3D onion diameter estimation."""
    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    NOT_SUPPORTED = "NOT_SUPPORTED"
    PHYSICAL_VALIDATION_BLOCKED = "PHYSICAL_VALIDATION_BLOCKED"
    ONION_DIAMETER_UNVALIDATED = "ONION_DIAMETER_UNVALIDATED"
