# Mandi Nyaay — AI & Inspection Engine

## 1. Purpose of this Repository
This repository houses the computer vision (CV) and inspection intelligence core for **MANDI NYAAY**. It is engineered to provide objective, verifiable, and mathematically sound agricultural inspection—specifically for crop sizing, physical measurement estimation, defect detection, and quality grading under real-world mandi (marketplace) conditions.


## 2. What Belongs Here
- **Computer Vision Pipelines**: Preprocessing, segmentation, feature extraction, and defect identification algorithms.
- **Physical Measurement & Calibration**: Lens undistortion, metric scale estimation using physical reference markers, dimensional analysis (diameter, volume, surface area), and weight estimation models.
- **Grading & Decision Engines**: Deterministic agricultural grading rules based on official standards (e.g., AGMARK, mandi specifications).
- **Model Training & Evaluation**: Reproducible training pipelines, model architectures, weight management, and validation suites.
- **Data Integrity & Verification**: Evidence packaging, audit log generation, and uncertainty/degradation scoring.

## 3. What Explicitly Does NOT Belong Here
To maintain clean architecture and strict separation of concerns, the following components are strictly excluded from this repository:
- **Mobile Applications**: Flutter, Kotlin, Android, Jetpack Compose, Gradle configurations.
- **Web Frontends**: UI dashboards, client-facing web portals.
- **Monolithic Backend / Web Services**: Generic backend business logic, database schemas (PostgreSQL), and web API servers (FastAPI/Django). Integration with backends or frontends will be managed through explicit contracts and clean interfaces.
- **Mock/Simulator Code**: Placeholder demos, mock datasets, or synthetic inspection generators.

## 4. Current Development Stage
- **Stage**: Foundation & Engineering Standards Specification.
- **Focus**: Setting up workspace architecture, rules, and baseline protocols prior to dependency initialization, model development, or pipeline implementation.

## 5. No-Dummy-Data Policy
This is a production-grade inspection system meant for real field trade.
- **Zero Fabrication**: No hardcoded counts, fake weights, simulated bounding boxes, fabricated confidence values, or mocked grades are permitted.
- **Verifiable Inputs**: Every result must be derived from genuine sensor inputs, verified model inference, calibrated physical math, or explicit human review.
- **Explicit Failure States**: When data is insufficient or unreliable, the system must return explicit states (`NOT_IMPLEMENTED`, `UNKNOWN`, `MANUAL_REVIEW`, `RETRY`, `CALIBRATION_INVALID`) rather than guessing.
