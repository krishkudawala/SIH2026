# Mandi Nyaay AI — Domain Contracts (Phase 0)

## Overview
This document specifies the typed data structures, failure modes, and lifecycle states for the Mandi Nyaay computer vision core.

## Core Models

### 1. `CaptureInput`
Encapsulates the raw capture evidence and metadata:
- `capture_id`: Unique identifier (UUID or deterministic hash).
- `image_path`: Filesystem path to the preserved raw capture image.
- `captured_at`: ISO timestamp of acquisition.
- `device_metadata`: Camera sensor, focal length, resolution.
- `session_metadata`: Mandi location, lot ID, operator notes.

### 2. `MarkerObservation`
Encapsulates reference marker (ArUco) detection and calibration geometry:
- `detected`: Boolean flag indicating if marker was found.
- `marker_id`: Decoded marker ID integer.
- `corners_px`: Sub-pixel corner coordinates `[(x0, y0), (x1, y1), (x2, y2), (x3, y3)]`.
- `physical_size_mm`: Known metric edge size.
- `validation_status`: `VALID`, `NOT_IMPLEMENTED`, `CALIBRATION_INVALID`, etc.
- `failure_code`: Specific failure code (`MARKER_NOT_DETECTED`, `GEOMETRY_INVALID`, etc.).

### 3. `ImageQualityObservation`
Encapsulates blur, exposure, and illumination integrity:
- `blur_measure`: Laplacian variance score.
- `brightness_measure`: Mean luminance value.
- `exposure_measure`: Clipping ratio.
- `quality_status`: `VALID`, `RETRY`, `INVALID_CAPTURE`, etc.
- `failure_codes`: List of triggered failure codes.

### 4. `OnionObservation`
Encapsulates single produce entity detection and measurement:
- `onion_id`: Unique produce ID.
- `boundary_px`: 2D polygon vertices of the contour.
- `bbox`: Coordinates `(xmin, ymin, xmax, ymax)`.
- `raw_pixel_measurements`: `area_px`, `major_axis_px`, `minor_axis_px`, `perimeter_px`.
- `calibrated_measurements`: `min_diameter_mm`, `max_diameter_mm`, `estimated_weight_g`.
- `measurement_status`: `NOT_IMPLEMENTED` in Phase 0.

### 5. `InspectionObservation`
Root observation combining all components:
- `capture_id`: Reference capture ID.
- `marker_result`: `MarkerObservation`.
- `quality_result`: `ImageQualityObservation`.
- `onion_observations`: List of `OnionObservation`.
- `processing_version`: Traceable code/pipeline version string.
- `overall_status`: Aggregate lifecycle status.

## Lifecycle & Failure States
- `VALID`: Pipeline step succeeded with high confidence.
- `NOT_IMPLEMENTED`: Model or detection phase is not yet built.
- `UNKNOWN`: Data is inconclusive or cannot be extracted.
- `MANUAL_REVIEW`: Borderline metrics requiring human inspection.
- `RETRY`: Image quality is degraded (blur, lighting); re-capture requested.
- `CALIBRATION_INVALID`: Reference marker missing or geometrically distorted.
- `INVALID_CAPTURE`: Image missing, unreadable, or corrupted.
