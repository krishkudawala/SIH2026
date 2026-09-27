# Mandi Nyaay AI — Deployment Strategy & Mobile Edge Architecture

## 1. Offline-First Field Reality
Mandi procurement centres, farmer fields, and rural warehouses routinely operate with zero cellular reception or intermittent 2G/3G connectivity. 
* **Core Requirement**: 100% of image validation, ArUco plane calibration, instance segmentation, measurement, defect classification, and rule-based grading must execute **locally on the inspector's Android device without calling any remote cloud API**.
* **Synchronization Model**: When connectivity is re-established (e.g., WiFi at the procurement office), the local tamper-evident event ledger syncs with central institutional repositories.

---

## 2. Edge Hardware Budget & Constraints

| Dimension | Target Specification | Hard Boundary / Limit |
|---|---|---|
| **Target OS** | Android 10+ (API level 29+) | Arm64-v8a architecture |
| **Peak RAM Usage** | $< 350\text{ MB}$ | Must not exceed $500\text{ MB}$ (prevents Android LMK kill) |
| **End-to-End Latency** | $< 1.5\text{ seconds}$ per tray capture | Must not exceed $3.0\text{ seconds}$ total |
| **Storage Footprint** | $< 80\text{ MB}$ total model/binary package | APK AI bundle limit $< 100\text{ MB}$ |
| **Processor Profile** | Mid-range Qualcomm Snapdragon (600/700 series) or MediaTek Dimensity | CPU execution baseline (FP32/INT8) + optional NNAPI/NPU acceleration |
| **Thermal / Battery** | Sustained operation over 4-hour procurement shift ($\ge 150$ captures) | Battery consumption $< 15\%$ per 100 inspections |

---

## 3. Two-Tier Repository & Artifact Lifecycle
To keep the production mobile application lean and secure, research tools and heavy training infrastructure are strictly segregated from the deployable inference bundle:

```
┌────────────────────────────────────────────────────────┐
│            RESEARCH & TRAINING REPOSITORY              │
│ (PyTorch, CVAT, SAM 2, Scikit-Learn, Full Resolution) │
└───────────────────────────┬────────────────────────────┘
                            │ Export & Verification
                            ▼
┌────────────────────────────────────────────────────────┐
│             DEPLOYABLE ARTIFACT PIPELINE               │
│ • PyTorch -> ONNX Export (`opset=17`)                  │
│ • Static Graph Optimization (ONNX Simplifier)          │
│ • Post-Training INT8 Quantization (PTQ)                │
│ • Parity Verification against FP32 ground truth        │
└───────────────────────────┬────────────────────────────┘
                            │ Versioned Bundle (.onnx + .json)
                            ▼
┌────────────────────────────────────────────────────────┐
│            MOBILE RUNTIME INFERENCE BUNDLE             │
│ (ONNX Runtime Mobile / OpenCV Android C++, < 35 MB)   │
└────────────────────────────────────────────────────────┘
```

---

## 4. Model Export & Optimization Workflow
1. **PyTorch to ONNX**: Export models using standard dynamic/fixed shape ONNX specifications:
   ```python
   torch.onnx.export(
       model,
       dummy_input,
       "model_deploy.onnx",
       opset_version=17,
       input_names=["input_tensor"],
       output_names=["boxes", "masks", "scores"],
   )
   ```
2. **Quantization & Benchmarking**:
   - Apply post-training INT8 quantization using representative field calibration images from **Dataset A** and **Dataset B**.
   - Verify that INT8 quantization degradation does not exceed $1.5\%$ mask mIoU or $0.5\text{ mm}$ measurement diameter discrepancy compared to full-precision FP32.
3. **Execution Runtime**: Execute via **ONNX Runtime Mobile (C++ / Java bindings)** or standalone OpenCV DNN module, ensuring zero dependency on Python runtime on the client device.
4. **Interface Contract**: The mobile application communicates with the inference core using the exact typed JSON schemas defined in `app/domain/models.py`.
