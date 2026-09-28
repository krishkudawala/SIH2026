import 'package:flutter/material.dart';
import 'package:sih2631/manid_nyaay/data/ui/components/mandi_app_bar.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/inspection/inspection_view_model.dart';

const Color backgroundGray = Color(0xFFF4F5F7);
const Color surfaceWhite = Colors.white;
const Color institutionalBlue = Color(0xFF1565C0);
const Color textPrimary = Color(0xFF1E293B);
const Color textSecondary = Color(0xFF64748B);
const Color textOnBlue = Colors.white;
const Color warnColor = Color(0xFFE65100);
const Color warnBg = Color(0xFFFFF3E0);
const Color warnBorder = Color(0xFFFFB74D);

class MeasurementWeightScreen extends StatelessWidget {
  final InspectionUiState uiState;
  final VoidCallback onProceed;
  final VoidCallback onBack;

  const MeasurementWeightScreen({
    super.key,
    required this.uiState,
    required this.onProceed,
    required this.onBack,
  });

  @override
  Widget build(BuildContext context) {
    final meas = uiState.measurementData ?? {};
    final weight = uiState.weightData ?? {};
    final obs = uiState.rawObservations;

    final sizeStatus = (meas['size_status'] ?? 'ONION_DIAMETER_UNVALIDATED').toString();
    final massStatus = (weight['mass_status'] ?? 'UNVALIDATED').toString();
    final isCalibrated = massStatus == 'CALIBRATED';

    final declaredWeightKg = uiState.certifiedLotWeightKg;
    final weighbridgeVarianceKg = (weight['weighbridge_variance_kg'] as num?)?.toDouble();
    final hasVariance = declaredWeightKg > 0 && weighbridgeVarianceKg != null;

    final piLow = (weight['prediction_interval_low_g'] as num?)?.toDouble();
    final piHigh = (weight['prediction_interval_high_g'] as num?)?.toDouble();

    return Scaffold(
      backgroundColor: backgroundGray,
      appBar: MandiTopAppBar(
        title: "Measurement & Weight",
        subtitle: "Dimensional & Gravimetric Status",
        showBack: true,
        onBack: onBack,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Size status
            _SectionStatusCard(
              label: "PHYSICAL DIAMETER",
              status: sizeStatus,
              description:
                  "Tri-axial dimensions (Major L, Minor W, Polar T) from segmentation contours. "
                  "Physical millimetric values are UNVALIDATED without an active ArUco "
                  "fiducial reference mat in frame.",
              icon: Icons.straighten,
            ),
            const SizedBox(height: 14),

            // Per-observation dimension table from REAL backend data
            if (obs.isNotEmpty) ...[
              Card(
                elevation: 1.0,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                color: surfaceWhite,
                child: Padding(
                  padding: const EdgeInsets.all(14.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        "PER-OBSERVATION DIMENSIONAL REPORT",
                        style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: textSecondary),
                      ),
                      const SizedBox(height: 2),
                      const Text(
                        "All values UNVALIDATED — no fiducial calibration detected.",
                        style: TextStyle(fontSize: 11, color: warnColor, fontWeight: FontWeight.w600),
                      ),
                      const SizedBox(height: 10),
                      const Row(
                        children: [
                          Expanded(flex: 3, child: Text("Obs ID", style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: textSecondary))),
                          Expanded(flex: 2, child: Text("Class", style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: textSecondary))),
                          Expanded(flex: 2, child: Text("Size(mm)", style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: textSecondary))),
                          Expanded(flex: 2, child: Text("Wt(g)*", style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: textSecondary))),
                        ],
                      ),
                      const Divider(height: 8),
                      ...obs.take(12).map((o) {
                        final id = (o['id'] ?? '???').toString();
                        final shortId = id.length > 8 ? id.substring(0, 8) : id;
                        final cond = (o['condition'] ?? '?').toString();
                        final sizeMm = (o['size_mm'] as num?)?.toStringAsFixed(1) ?? '—';
                        final weightG = (o['weight_g'] as num?)?.toStringAsFixed(1) ?? '—';
                        return Padding(
                          padding: const EdgeInsets.symmetric(vertical: 3),
                          child: Row(
                            children: [
                              Expanded(flex: 3, child: Text(shortId, style: const TextStyle(fontSize: 11, fontFamily: 'monospace', color: institutionalBlue))),
                              Expanded(flex: 2, child: Text(cond, style: const TextStyle(fontSize: 11))),
                              Expanded(flex: 2, child: Text(sizeMm, style: const TextStyle(fontSize: 11))),
                              Expanded(flex: 2, child: Text(weightG, style: const TextStyle(fontSize: 11))),
                            ],
                          ),
                        );
                      }),
                      if (obs.length > 12)
                        Text("… and ${obs.length - 12} more",
                            style: const TextStyle(fontSize: 11, color: textSecondary)),
                      const SizedBox(height: 4),
                      const Text(
                        "* Weight is UNVALIDATED model estimate, not physical scale reading.",
                        style: TextStyle(fontSize: 10, color: warnColor),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 14),
            ],

            // Weighbridge variance card — only if declared weight exists
            if (declaredWeightKg > 0) ...[
              Card(
                elevation: 1.0,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                color: surfaceWhite,
                child: Padding(
                  padding: const EdgeInsets.all(14.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        "WEIGHBRIDGE RECORD — REVIEW SIGNAL",
                        style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: textSecondary),
                      ),
                      const SizedBox(height: 6),
                      _DataRow(label: "Declared/Certified Weight", value: "${declaredWeightKg.toStringAsFixed(1)} kg"),
                      if (hasVariance)
                        _DataRow(
                          label: "Weighbridge Variance",
                          value: "${weighbridgeVarianceKg.toStringAsFixed(1)} kg",
                          highlight: weighbridgeVarianceKg.abs() > 50,
                        ),
                      const SizedBox(height: 6),
                      const Text(
                        "Variance is a REVIEW SIGNAL only. Never labeled as fraud.",
                        style: TextStyle(fontSize: 11, color: warnColor, fontWeight: FontWeight.w600),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 14),
            ],

            // Mass status
            _SectionStatusCard(
              label: "MASS & WEIGHT STATUS",
              status: "MASS: $massStatus",
              description: isCalibrated
                  ? "Weight model is calibrated with physical scale data."
                  : "Gravimetric mass estimation is UNVALIDATED. "
                      "No paired digital scale calibration exists. "
                      "Mandi Nyaay will never invent or fabricate mass estimates.",
              icon: Icons.scale,
              isWarning: !isCalibrated,
            ),
            const SizedBox(height: 14),

            // Prediction interval — only when calibrated
            if (isCalibrated && piLow != null && piHigh != null) ...[
              Card(
                color: const Color(0xFFE8F5E9),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(10),
                  side: const BorderSide(color: Color(0xFFA5D6A7)),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(14),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text("PREDICTION INTERVAL (CALIBRATED)",
                          style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Color(0xFF2E7D32))),
                      const SizedBox(height: 6),
                      Text("${piLow.toStringAsFixed(1)} g — ${piHigh.toStringAsFixed(1)} g",
                          style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Color(0xFF1B5E20))),
                      const Text("Conformal prediction interval at configured coverage target.",
                          style: TextStyle(fontSize: 11, color: Color(0xFF388E3C))),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 14),
            ],

            // Statutory guarantee banner
            Container(
              padding: const EdgeInsets.all(14.0),
              decoration: BoxDecoration(
                color: const Color(0xFFE8F5E9),
                borderRadius: BorderRadius.circular(8.0),
                border: Border.all(color: const Color(0xFFA5D6A7)),
              ),
              child: const Row(
                children: [
                  Icon(Icons.shield, color: Color(0xFF2E7D32), size: 20),
                  SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      "Mandi Nyaay Strict Truthfulness Policy: Uncalibrated dimensions and masses are never disguised as verified numbers.",
                      style: TextStyle(fontSize: 11, color: Color(0xFF1B5E20), fontWeight: FontWeight.w600),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),

            ElevatedButton(
              onPressed: onProceed,
              style: ElevatedButton.styleFrom(
                backgroundColor: institutionalBlue,
                foregroundColor: textOnBlue,
                minimumSize: const Size(double.infinity, 48),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
              ),
              child: const Text("PROCEED TO REVIEW QUEUE", style: TextStyle(fontWeight: FontWeight.bold)),
            ),
          ],
        ),
      ),
    );
  }
}

class _SectionStatusCard extends StatelessWidget {
  final String label;
  final String status;
  final String description;
  final IconData icon;
  final bool isWarning;

  const _SectionStatusCard({
    required this.label,
    required this.status,
    required this.description,
    required this.icon,
    this.isWarning = true,
  });

  @override
  Widget build(BuildContext context) {
    final bg = isWarning ? warnBg : const Color(0xFFE8F5E9);
    final border = isWarning ? warnBorder : const Color(0xFFA5D6A7);
    final textColor = isWarning ? warnColor : const Color(0xFF2E7D32);

    return Card(
      elevation: 2.0,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      color: surfaceWhite,
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(children: [
                  Icon(icon, size: 18, color: textSecondary),
                  const SizedBox(width: 6),
                  Text(label,
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: textSecondary)),
                ]),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: bg,
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: border),
                  ),
                  child: Text(status,
                      style: TextStyle(color: textColor, fontWeight: FontWeight.bold, fontSize: 11)),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Text(description, style: const TextStyle(fontSize: 12, color: textSecondary)),
          ],
        ),
      ),
    );
  }
}

class _DataRow extends StatelessWidget {
  final String label;
  final String value;
  final bool highlight;
  const _DataRow({required this.label, required this.value, this.highlight = false});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(fontSize: 12, color: textSecondary)),
          Text(value,
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.bold,
                color: highlight ? Colors.red : textPrimary,
              )),
        ],
      ),
    );
  }
}
