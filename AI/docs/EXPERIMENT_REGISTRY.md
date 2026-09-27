# Mandi Nyaay AI — Experiment Registry & Engineering Targets

## 1. Registry Policy
* **Zero Premature Claims**: No target is ever reported as "achieved" or "validated" until supported by reproducible empirical measurement on real field datasets.
* **Status Lifecycle**:
  - `UNVALIDATED`: Proposed engineering target based on operational requirements. Zero field data measured.
  - `MEASURED`: Evaluated on a specific real-world dataset batch. Numerical results recorded with known variance and failure cases.
  - `VALIDATED`: Consistently cleared across multiple independent held-out field sessions/mandis under the Hard Acceptance Gate protocol.

---

## 2. Active Engineering Target Registry

| Target ID | Parameter / Metric | Proposed Target | Operational Justification | Measurement Method | Required Dataset / Experiment | Current Measured Value | Current Status |
|---|---|---|---|---|---|---|---|
| **TRG-G1-01** | Marker Detection Reliability | $\ge 98\%$ on unoccluded views | Field captures must not fail calibration under standard handheld angles | Proportion of detected markers across valid test captures ($<30^\circ$ tilt) | **DATASET G1**: Real smartphone captures across distances (35–65 cm) and angles | `None` (Awaiting physical field captures) | **UNVALIDATED** |
| **TRG-G1-02** | Corner Jitter Repeatability | Standard deviation $< 0.8\text{ px}$ | Corner stability is vital for low-variance planar homography | Sub-pixel corner coordinate dispersion across static multi-frame burst captures | **DATASET G1**: 10-shot static bursts per lighting condition | `None` (Awaiting physical field captures) | **UNVALIDATED** |
| **TRG-G1-03** | Planar Metric Error | Absolute relative error $\le 1.0\%$ | Tray-level distance measurement must be reliable before attempting 3D produce sizing | $|\text{Measured}_{\text{mm}} - \text{True}_{\text{mm}}| / \text{True}_{\text{mm}} \times 100\%$ on physical reference disc | **DATASET G1**: Planar homography against vernier-measured metal calibration disc | `None` (Awaiting physical field captures) | **UNVALIDATED** |
| **TRG-G1-04** | Reprojection Residual | RMS reprojection error $< 1.5\text{ px}$ | Confirms projective homography accurately models lens-plane perspective | RMS Euclidean distance between detected corners and back-projected marker metric corners | **DATASET G1**: Homography estimation from 4 detected corners | `None` (Awaiting physical field captures) | **UNVALIDATED** |
| **TRG-G2-01** | Severe Blur Rejection | $100\%$ rejection of severe motion blur | Blurry frames produce inaccurate boundaries and misleading defect classifications | Rejection rate (`RETRY` / `BLUR_EXCEEDED`) on intentionally blurred field captures | **DATASET G2**: Paired sharp vs. blurred captures across varying shutter speeds | `None` (Awaiting physical field captures) | **UNVALIDATED** |
| **TRG-G2-02** | Exposure Clipping Rejection | Rejection of frames with $> 8\%$ clipped pixels | Severe overexposure (glare) and underexposure obliterate texture | Proportion of black/saturated pixels exceeding threshold | **DATASET G2**: Paired normal vs. clipped field captures | `None` (Awaiting physical field captures) | **UNVALIDATED** |
| **TRG-G3-01** | Instance Mask mIoU | Mean IoU $\ge 0.88$ | Individual bulb boundaries directly dictate calculated equatorial diameter | Standard Intersection-over-Union against human-verified gold polygon masks | **DATASET G3**: Held-out split of touching/overlapping field onions | `None` (Awaiting segmentation model & data) | **UNVALIDATED** |
| **TRG-G3-02** | Clustered Merge Error Rate | Under-segmentation rate $< 2.0\%$ | Merging two touching bulbs creates false jumbo sizes and distorts weight | Count of merged bulb instances divided by total true bulb instances | **DATASET G3**: Clustered and touching onion lots | `None` (Awaiting segmentation model & data) | **UNVALIDATED** |
| **TRG-G5-01** | Equatorial Diameter Error | MAE $\le 1.5\text{ mm}$ | Sizing into standard commercial grade bands requires millimeter accuracy | Mean Absolute Error against vernier caliper physical ground truth | **DATASET G5**: Multi-view calibrated captures with caliper measurements | `None` (Awaiting measurement engine & data) | **UNVALIDATED** |
| **TRG-G6-01** | Weight Estimation Error | MAPE $\le 7.0\%$, MAE $\le 8\text{ g}$ | Lot weight estimation must reconcile against weighbridge tolerance | Mean Absolute Percentage Error against certified digital scale weight | **DATASET G5**: Individual bulb digital scale weights ($0.1\text{g}$ resolution) | `None` (Awaiting weight calibration engine & data) | **UNVALIDATED** |
| **TRG-G7-01** | External Defect Precision | Macro-averaged Precision $\ge 0.85$ | False defect calls unfairly penalize farmer lots into lower grades | Macro precision across 6 defect classes on human-adjudicated test set | **DATASET G6**: Diverse defect specimens verified by agronomists | `None` (Awaiting defect model & data) | **UNVALIDATED** |
| **TRG-G11-01** | Mobile Peak RSS RAM | Benchmark target $< 350\text{ MB}$ | Prevent Android Low Memory Killer (LMK) from aborting the app on 3GB RAM phones | Runtime memory profiling using Android `dumpsys meminfo` during 50-tray stress test | **DATASET G1–G6**: On-device benchmark on reference target hardware | `None` (Awaiting mobile benchmark phase) | **UNVALIDATED** |
| **TRG-G11-02** | End-to-End Tray Latency | Latency $< 2.0\text{ s}$ per tray capture | Minimizes inspector wait time to maintain high mandi throughput | Wall-clock elapsed time from shutter release to structured observation emit | **DATASET G1–G6**: Mid-range reference smartphone (Snapdragon 680 / Helio G99) | `None` (Awaiting mobile benchmark phase) | **UNVALIDATED** |

---

## 3. Benchmark Registry Update Protocol
When an experiment is performed:
1. Record git commit hash, date, hardware environment, and raw dataset URI.
2. Update **Current Measured Value** with empirical statistics (mean, standard deviation, sample size $N$).
3. Transition status from `UNVALIDATED` to `MEASURED`.
4. Only promote to `VALIDATED` after the result is replicated across multiple independent procurement sessions.
