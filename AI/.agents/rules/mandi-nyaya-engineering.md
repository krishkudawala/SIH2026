# Mandi Nyaay AI & Inspection Core — Permanent Engineering Rules

## 1. Workspace Boundary & Isolation
- This repository is the dedicated, independent AI/CV/inspection intelligence core for **MANDI NYAAY**.
- **Strict Boundary**: This workspace must NOT depend on, import, modify, or contain code for:
  - Mobile client applications (Flutter, Kotlin, Jetpack Compose, Gradle, Android)
  - Frontend web applications
  - External monolithic backend services (FastAPI web services, PostgreSQL schemas, external business logic)
- Integration with external services or client apps will occur exclusively via clean, explicit, and versioned interfaces/contracts.

## 2. Non-Negotiable Anti-Fabrication Rule (Ground Truth Policy)
Every output produced by this system must strictly reflect ground reality.
**NEVER fabricate, synthesize, or hardcode:**
- Produce counts (e.g., onion counts)
- Physical measurements (dimensions, diameter, volume, surface area)
- Model inferences, classifications, or bounding boxes
- Confidence scores or probability values
- Weights, density estimates, or mass calculations
- Commercial quality grades
- Statistical results, benchmarks, or validation metrics
- Camera or scale calibration matrices/results
- Evidentiary records or audit logs
- Synchronization or state representations

Every output must originate from one of the following:
1. Real input data (captured images, sensor streams)
2. Real physical measurements (calibrated references, physical scales)
3. Real model inference (validated neural network weights / machine learning models)
4. Real deterministic computation (geometry algorithms, mathematical transformations)
5. Real persisted state (verified storage)
6. Explicit human input (annotator, inspector, or operator)

## 3. Explicit Failure States & Graceful Degradation
When an algorithm cannot compute a reliable, high-integrity result, it must **never guess or interpolate silently**.
The system must explicitly return formal failure or review states, including but not limited to:
- `NOT_IMPLEMENTED`: Subsystem or feature path is not yet built.
- `UNKNOWN`: The data is inconclusive or features cannot be reliably extracted.
- `MANUAL_REVIEW`: Quality parameters fall near boundary thresholds or show anomalies requiring human inspector review.
- `RETRY`: Image quality (blur, glare, occlusion, lighting) is insufficient for accurate assessment.
- `CALIBRATION_INVALID`: Reference markers, scale cards, or extrinsic/intrinsic parameters cannot be validated.

## 4. Real Data Before Demos
- Never build smoke-and-mirrors or simulated demonstrations.
- Pipelines must be designed, tested, and validated against genuine field imagery and real physical measurements before any demonstration or deployment.

## 5. Explicit Confidence & Surfaced Uncertainty
- Confidence scores must represent calibrated model outputs or rigorous deterministic error bounds.
- Hardcoded confidence values (e.g., arbitrarily returning `0.95` or `0.98`) are strictly prohibited.
- Surfacing uncertainty is mandatory: expose error intervals, image degradation factors (e.g., motion blur index, lighting deficiency), and occlusion metrics.

## 6. Model Performance & Benchmarking Integrity
- No fabricated accuracy, precision, recall, or F1 scores.
- All performance figures must be derived from reproducible evaluations on well-characterized, versioned evaluation sets.

## 7. No Placeholder Computer Vision Presented as Real
- Never mock bounding boxes, segmentations, keypoints, or defect heatmaps in pipeline outputs.
- If a model is not invoked or not ready, state `NOT_IMPLEMENTED` or `MANUAL_REVIEW`.

## 8. Preservation of Raw Evidence
- Agricultural trade disputes demand verifiable proof.
- Retain raw input frames, calibration metadata, preprocessing parameters, and intermediate inference representations required for deterministic auditability and dispute resolution.

## 9. Comprehensive Versioning & Traceability
Every inspection result must be fully traceable to:
- Pipeline / processing algorithm version
- Model architecture and model weights hash/checksum
- Decision rule / grading standard version
- Calibration profile and reference parameters

## 10. Reproducibility & Rigorous Testing
- All experiments, pipelines, and evaluation runs must be strictly reproducible (fixed seeds, tracked hyperparameters, recorded environment manifests).
- Write comprehensive tests for mathematical formulas, coordinate transforms, calibration logic, and deterministic rule engines.

## 11. Human-in-the-Loop Optimization
- Design algorithms to minimize manual farmer and inspector effort without stripping away human oversight.
- The human operator remains the final authority; the inspection engine provides verified, objective, and auditable intelligence.
